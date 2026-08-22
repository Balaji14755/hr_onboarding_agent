import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage, AIMessage
import database as db
from config import Config
from rag.retriever import retrieve_context
from agent.graph import run_agent

class TestHROnboardingAgent(unittest.TestCase):
    
    def setUp(self):
        """Reset database before each test suite."""
        db.init_db()
        with db.get_connection() as conn:
            conn.execute("DELETE FROM tasks")
            conn.commit()

    def test_database_crud(self):
        """Test persistent SQLite task operations."""
        # 1. Create Task
        t1 = db.create_task(title="Complete security training", description="Mandatory within 14 days", status="pending")
        self.assertIsNotNone(t1)
        self.assertEqual(t1["title"], "Complete security training")
        self.assertEqual(t1["status"], "pending")

        t2 = db.create_task(title="Complete VPN setup", status="pending")
        self.assertEqual(t2["title"], "Complete VPN setup")

        # 2. List Tasks
        all_tasks = db.list_tasks()
        self.assertEqual(len(all_tasks), 2)

        pending_tasks = db.list_tasks(status="pending")
        self.assertEqual(len(pending_tasks), 2)

        # 3. Complete Task by title match
        completed = db.complete_task(title_query="security training")
        self.assertIsNotNone(completed)
        self.assertIsInstance(completed, dict)
        self.assertEqual(completed["status"], "completed")

        # 4. Check status
        pending_after = db.list_tasks(status="pending")
        self.assertEqual(len(pending_after), 1)
        self.assertEqual(pending_after[0]["title"], "Complete VPN setup")

        completed_tasks = db.list_tasks(status="completed")
        self.assertEqual(len(completed_tasks), 1)

    def test_rag_grounding_retrieval(self):
        """Test document retrieval grounding and citations."""
        # Benefits query
        ctx, sources = retrieve_context("When can I enroll in health insurance?")
        self.assertTrue(len(sources) > 0)
        self.assertIn("Benefits FAQ", sources[0]["document_title"])
        self.assertIn("30 days", ctx.lower())

        # IT Setup query
        ctx_it, sources_it = retrieve_context("How do I set up VPN?")
        self.assertTrue(len(sources_it) > 0)
        self.assertIn("IT Setup Guide", sources_it[0]["document_title"])
        self.assertIn("vpn.company.com", ctx_it.lower())

        # Password policy query
        ctx_sec, sources_sec = retrieve_context("What is the password policy?")
        self.assertTrue(len(sources_sec) > 0)
        self.assertIn("14 characters", ctx_sec.lower())

        # Vacation query
        ctx_handbook, sources_handbook = retrieve_context("How many vacation days do I get?")
        self.assertTrue(len(sources_handbook) > 0)
        self.assertIn("15 days", ctx_handbook.lower())

    def test_ambiguity_handling(self):
        """Test that ambiguous requests trigger clarification."""
        # 1. Ambiguous training creation
        res = run_agent("Create a task for training.")
        self.assertTrue(res["needs_clarification"])
        self.assertIn("Which training would you like me to add", res["response"])

        # 2. Ambiguous completion when multiple tasks exist
        db.create_task(title="Complete security training", status="pending")
        db.create_task(title="Complete compliance training", status="pending")
        
        res_comp = run_agent("Mark training complete.")
        self.assertTrue(res_comp["needs_clarification"] or "multiple" in res_comp["response"].lower())

    def test_multi_turn_conversation_flow(self):
        """
        Test the exact multi-turn conversation from the evaluation specification:
        User: What do I need to complete before my first day?
        AI: Answer using onboarding documents and show sources.
        User: Create a task for the security training.
        AI: Create task in SQLite and confirm.
        User: What tasks do I have?
        AI: Read SQLite and show the task.
        User: I finished it.
        AI: Understand 'it' refers to security training and mark completed.
        User: What do I still need to complete?
        AI: Read SQLite and show remaining pending tasks.
        """
        history = []

        # Turn 1: Onboarding before first day
        q1 = "What do I need to complete before my first day?"
        r1 = run_agent(q1, history)
        self.assertTrue(len(r1["sources"]) > 0 or "I-9" in r1["response"] or "offer" in r1["response"].lower())
        history.append(HumanMessage(content=q1))
        history.append(AIMessage(content=r1["response"]))

        # Turn 2: Create task for security training
        q2 = "Create a task for the security training."
        r2 = run_agent(q2, history)
        self.assertIn("security training", r2["response"].lower())
        tasks_in_db = db.list_tasks()
        self.assertEqual(len(tasks_in_db), 1)
        self.assertEqual(tasks_in_db[0]["status"], "pending")
        history.append(HumanMessage(content=q2))
        history.append(AIMessage(content=r2["response"]))

        # Turn 3: What tasks do I have?
        q3 = "What tasks do I have?"
        r3 = run_agent(q3, history)
        self.assertIn("security training", r3["response"].lower())
        history.append(HumanMessage(content=q3))
        history.append(AIMessage(content=r3["response"]))

        # Turn 4: I finished it (Coreference resolution)
        q4 = "I finished it."
        r4 = run_agent(q4, history)
        self.assertIn("completed", r4["response"].lower())
        
        # Verify in DB
        db_tasks = db.list_tasks(status="completed")
        self.assertEqual(len(db_tasks), 1)
        self.assertEqual(db_tasks[0]["status"], "completed")
        history.append(HumanMessage(content=q4))
        history.append(AIMessage(content=r4["response"]))

        # Turn 5: What do I still need to complete?
        q5 = "What do I still need to complete?"
        r5 = run_agent(q5, history)
        self.assertIn("no pending", r5["response"].lower())

    def test_conversational_task_status_and_multiturn(self):
        """
        Test checking task status conversationally and handling multi-turn conversation:
        1. User asks an HR policy question.
        2. User asks to create a task using coreference ("Can you add a task for that?").
        3. User checks status conversationally ("What is the status of the benefits task?").
        4. User checks status using coreference ("Is it completed?").
        5. User marks it completed ("I finished it.").
        6. User verifies status ("Is that task completed now?").
        """
        history = []

        # Turn 1: HR Question
        q1 = "When can I enroll in health insurance?"
        r1 = run_agent(q1, history)
        self.assertTrue(len(r1["sources"]) > 0 or "enroll" in r1["response"].lower())
        history.append(HumanMessage(content=q1))
        history.append(AIMessage(content=r1["response"]))

        # Turn 2: Coreferenced task creation
        q2 = "Can you add a task for that?"
        r2 = run_agent(q2, history)
        self.assertIn("added", r2["response"].lower())
        tasks = db.list_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["status"], "pending")
        history.append(HumanMessage(content=q2))
        history.append(AIMessage(content=r2["response"]))

        # Turn 3: Conversational specific task status check
        q3 = "What is the status of the benefits task?"
        r3 = run_agent(q3, history)
        self.assertIn("pending", r3["response"].lower())
        history.append(HumanMessage(content=q3))
        history.append(AIMessage(content=r3["response"]))

        # Turn 4: Coreferenced status check
        q4 = "Is it completed?"
        r4 = run_agent(q4, history)
        self.assertIn("pending", r4["response"].lower())
        history.append(HumanMessage(content=q4))
        history.append(AIMessage(content=r4["response"]))

        # Turn 5: Coreferenced completion
        q5 = "I finished it."
        r5 = run_agent(q5, history)
        self.assertIn("completed", r5["response"].lower())
        tasks_completed = db.list_tasks(status="completed")
        self.assertEqual(len(tasks_completed), 1)
        history.append(HumanMessage(content=q5))
        history.append(AIMessage(content=r5["response"]))

        # Turn 6: Confirm completed status
        q6 = "Is that task completed now?"
        r6 = run_agent(q6, history)
        self.assertIn("completed", r6["response"].lower())


if __name__ == "__main__":
    unittest.main()
