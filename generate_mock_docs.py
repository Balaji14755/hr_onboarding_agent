import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from config import Config

class NumberedCanvas(canvas.Canvas):
    """Custom canvas that adds page numbers and confidentiality header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Header
        self.drawString(54, 755, "ACME CORP — INTERNAL ONBOARDING & HR POLICY [MOCK DOCUMENT]")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 747, letter[0] - 54, 747)

        # Footer
        self.line(54, 45, letter[0] - 54, 45)
        self.setFont("Helvetica", 8)
        self.drawString(54, 32, "Confidential - For Internal Employee Use Only")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()


def get_styles():
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=6,
        spaceBefore=0
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#2C5282")
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "h1": h1_style,
        "h2": h2_style,
        "body": body_style,
        "bullet": bullet_style,
        "callout": callout_style
    }


def create_callout_box(text, styles):
    content = Paragraph(text, styles["callout"])
    table = Table([[content]], colWidths=[500])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EBF8FF")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#BEE3F8")),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    return table


def build_benefits_faq(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=54
    )
    styles = get_styles()
    story = []

    # PAGE 1: Health, Dental, Vision & Eligibility
    story.append(Paragraph("Employee Benefits FAQ & Enrollment Guide", styles["title"]))
    story.append(Paragraph("Comprehensive Summary of Health, Dental, Vision, and Wellness Programs", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=10))

    story.append(Paragraph("1. Eligibility for Employee Benefits", styles["h1"]))
    story.append(Paragraph(
        "All regular full-time employees working 30 or more hours per week are eligible to participate in Acme Corp benefit plans. "
        "Coverage begins on the first day of the calendar month following your hire date. Part-time employees working fewer than 30 hours per week and temporary contractors are not eligible for health and welfare benefits.",
        styles["body"]
    ))

    story.append(Paragraph("2. Enrollment Period & Deadlines", styles["h1"]))
    story.append(Paragraph(
        "New employees must complete their benefit elections within their first 30 days of employment via the HR Benefits Portal (https://benefits.company.com). "
        "If you do not enroll within your 30-day enrollment window, you will automatically be defaulted into basic employee-only high-deductible healthcare coverage and will not be able to make changes until the next annual Open Enrollment period.",
        styles["body"]
    ))
    story.append(Paragraph(
        "Annual Open Enrollment takes place every year from November 1 through November 15, with changes taking effect on January 1 of the following year. Mid-year changes are only permitted within 30 days of a Qualifying Life Event (QLE) such as marriage, birth of a child, divorce, or loss of spouse's coverage.",
        styles["body"]
    ))

    story.append(Paragraph("3. Health Insurance Coverage", styles["h1"]))
    story.append(Paragraph(
        "Acme Corp offers two comprehensive medical plan options administered through Blue Cross Blue Shield:",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Premier PPO Plan:</b> Low deductible ($500 individual / $1,000 family). In-network preventive care is 100% covered. Primary care copay is $20; specialist copay is $40. Out-of-pocket maximum is $3,000 individual / $6,000 family.", styles["bullet"]))
    story.append(Paragraph("• <b>HDHP with HSA Plan:</b> High-deductible health plan ($1,500 individual / $3,000 family). In-network preventive care is 100% covered. Acme Corp contributes $1,000 (individual) or $2,000 (family) annually to your Health Savings Account (HSA).", styles["bullet"]))

    story.append(Spacer(1, 10))
    story.append(create_callout_box("<b>Important Note on Health Enrollment:</b> To add dependents, you must provide supporting documentation (marriage certificate, birth certificate) to hr-benefits@company.com within 30 days of hire.", styles))

    story.append(PageBreak())

    # PAGE 2: Dental, Vision, Dependents & Retirement
    story.append(Paragraph("4. Dental & Vision Insurance", styles["h1"]))
    story.append(Paragraph("• <b>Dental Plan (Delta Dental PPO):</b> Preventive cleanings and annual checkups are covered at 100% (2 per calendar year). Basic services (fillings, extractions) are covered at 80%. Major services (crowns, bridges, root canals) are covered at 50%. The annual maximum benefit is $2,000 per covered person.", styles["bullet"]))
    story.append(Paragraph("• <b>Vision Plan (VSP Vision Care):</b> Annual comprehensive eye exams are covered with a $10 copay. Prescription lenses are covered with a $25 copay. Frame and contact lens allowance provides up to $200 every 12 months.", styles["bullet"]))

    story.append(Paragraph("5. Dependent Coverage", styles["h1"]))
    story.append(Paragraph(
        "Employees may enroll eligible dependents in medical, dental, and vision plans. Eligible dependents include:",
        styles["body"]
    ))
    story.append(Paragraph("• Legal spouse or registered domestic partner (same or opposite sex).", styles["bullet"]))
    story.append(Paragraph("• Biological children, adopted children, stepchildren, and legal wards up to age 26, regardless of student or marital status.", styles["bullet"]))
    story.append(Paragraph("• Incapacitated dependent children over age 26 with physician certification.", styles["bullet"]))

    story.append(Paragraph("6. Flexible Spending Accounts (FSA)", styles["h1"]))
    story.append(Paragraph(
        "• <b>Healthcare FSA:</b> Contribute up to $3,200 pre-tax annually for eligible out-of-pocket medical, dental, and vision expenses (available only to PPO participants).",
        styles["bullet"]
    ))
    story.append(Paragraph(
        "• <b>Dependent Care FSA:</b> Contribute up to $5,000 pre-tax annually per household for qualified child day care or elder care expenses.",
        styles["bullet"]
    ))

    story.append(Paragraph("7. 401(k) Retirement Savings Plan", styles["h1"]))
    story.append(Paragraph(
        "Employees are eligible to participate in the Acme 401(k) Retirement Plan starting on their first day. Acme Corp matches 100% of employee contributions up to the first 4% of eligible salary. Company matching contributions vest over a 3-year graded vesting schedule (33% year 1, 66% year 2, 100% year 3). Both Traditional pre-tax and Roth after-tax contribution options are supported.",
        styles["body"]
    ))

    story.append(Spacer(1, 10))
    story.append(create_callout_box("<b>Benefits Support Contact:</b> For questions regarding benefits, claims, or life event changes, reach out to hr-benefits@company.com or schedule a 1-on-1 consultation via the Benefits Portal.", styles))

    doc.build(story, canvasmaker=NumberedCanvas)


def build_it_setup_guide(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=54
    )
    styles = get_styles()
    story = []

    # PAGE 1: Email, Laptop, VPN, MFA
    story.append(Paragraph("IT Setup & Technical Onboarding Guide", styles["title"]))
    story.append(Paragraph("Step-by-step instructions for hardware, corporate credentials, VPN, and security tools", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=10))

    story.append(Paragraph("1. Company Email & Account Setup", styles["h1"]))
    story.append(Paragraph(
        "Your company email account and Single Sign-On (SSO) profile are provisioned 3 business days before your start date. "
        "Your official email address follows the standard corporate format: <b>firstname.lastname@company.com</b>. "
        "To activate your account, navigate to https://identity.company.com and enter your temporary login credentials provided in your welcome email.",
        styles["body"]
    ))

    story.append(Paragraph("2. Laptop Hardware & Device Enrollment", styles["h1"]))
    story.append(Paragraph(
        "New hires receive either an Apple MacBook Pro 14\" (Apple Silicon) or Lenovo ThinkPad T14 (Windows 11). "
        "When turning on your laptop for the first time:",
        styles["body"]
    ))
    story.append(Paragraph("• Connect to a stable high-speed Wi-Fi network.", styles["bullet"]))
    story.append(Paragraph("• Follow the Automated Device Enrollment screen (Jamf for macOS, Microsoft Intune for Windows).", styles["bullet"]))
    story.append(Paragraph("• Log in with your company email credentials to apply security policies and corporate software profiles automatically.", styles["bullet"]))
    story.append(Paragraph("• Full-disk encryption (FileVault on macOS, BitLocker on Windows) is automatically activated and cannot be disabled.", styles["bullet"]))

    story.append(Paragraph("3. Multi-Factor Authentication (MFA) Setup", styles["h1"]))
    story.append(Paragraph(
        "MFA is mandatory on all corporate accounts and applications. During your initial login at https://identity.company.com/mfa:",
        styles["body"]
    ))
    story.append(Paragraph("• Download and install <b>Okta Verify</b> on your mobile device (iOS App Store or Google Play Store).", styles["bullet"]))
    story.append(Paragraph("• Scan the on-screen QR code to bind your mobile device to your Acme SSO account.", styles["bullet"]))
    story.append(Paragraph("• Enable biometric approval (Face ID / Fingerprint) and push notifications for seamless one-tap login authentication.", styles["bullet"]))

    story.append(Paragraph("4. Virtual Private Network (VPN) Setup", styles["h1"]))
    story.append(Paragraph(
        "A secure VPN connection is required to access internal corporate networks, development databases, and private git repositories when working remotely.",
        styles["body"]
    ))
    story.append(Paragraph("• Open the pre-installed <b>Cisco AnyConnect</b> (or GlobalProtect) application on your corporate laptop.", styles["bullet"]))
    story.append(Paragraph("• In the server address field, enter: <b>vpn.company.com</b>", styles["bullet"]))
    story.append(Paragraph("• Click 'Connect' and enter your Acme email and password when prompted.", styles["bullet"]))
    story.append(Paragraph("• Approve the push notification on your Okta Verify mobile app to establish the encrypted tunnel.", styles["bullet"]))

    story.append(PageBreak())

    # PAGE 2: Password Policy, Software & IT Support
    story.append(Paragraph("5. Password Requirements & Password Manager", styles["h1"]))
    story.append(Paragraph(
        "All corporate user accounts must strictly adhere to the following password policy requirements:",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Minimum Length:</b> Must be at least 14 characters long.", styles["bullet"]))
    story.append(Paragraph("• <b>Complexity:</b> Must contain at least one uppercase letter (A-Z), one lowercase letter (a-z), one numeral (0-9), and one special character (!@#$%^&*).", styles["bullet"]))
    story.append(Paragraph("• <b>Expiration:</b> Passwords must be changed every 90 days.", styles["bullet"]))
    story.append(Paragraph("• <b>History:</b> You cannot reuse any of your previous 6 passwords.", styles["bullet"]))
    story.append(Paragraph("• <b>Password Manager:</b> Acme provides an enterprise license for <b>1Password</b>. Store all work credentials in 1Password; never store passwords in plaintext or in web browsers.", styles["bullet"]))

    story.append(Paragraph("6. Approved Collaboration & Software Tools", styles["h1"]))
    story.append(Paragraph(
        "Your machine comes pre-configured with the standard corporate software suite:",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Communication:</b> Slack (channels #general, #announcements, #helpdesk) and Zoom.", styles["bullet"]))
    story.append(Paragraph("• <b>Productivity:</b> Google Workspace (Gmail, Docs, Drive, Calendar) and Microsoft 365.", styles["bullet"]))
    story.append(Paragraph("• <b>Project Management:</b> Jira, Confluence, and GitHub Enterprise.", styles["bullet"]))

    story.append(Paragraph("7. IT Support & Helpdesk Contact Info", styles["h1"]))
    story.append(Paragraph(
        "If you experience technical issues, hardware faults, or account lockouts, contact IT Support through any of the following channels:",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Helpdesk Portal:</b> https://helpdesk.company.com (Submit tickets & track resolution)", styles["bullet"]))
    story.append(Paragraph("• <b>Email Support:</b> it-support@company.com (Response within 2 hours during business hours)", styles["bullet"]))
    story.append(Paragraph("• <b>Slack Channel:</b> #it-helpdesk (Quick questions and live engineer support)", styles["bullet"]))
    story.append(Paragraph("• <b>Support Hours:</b> Monday through Friday, 8:00 AM – 6:00 PM EST", styles["bullet"]))
    story.append(Paragraph("• <b>Emergency IT Hotline:</b> 1-800-555-0199 (Available 24/7 for urgent access issues)", styles["bullet"]))

    story.append(Spacer(1, 10))
    story.append(create_callout_box("<b>IT Tip:</b> Keep your laptop plugged in and connected to Wi-Fi on your first night so mandatory system updates and security patches install without interrupting your workday.", styles))

    doc.build(story, canvasmaker=NumberedCanvas)


def build_employee_handbook(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=54
    )
    styles = get_styles()
    story = []

    # PAGE 1: Working Hours, Attendance, Leave Policy
    story.append(Paragraph("Employee Handbook & HR Policies", styles["title"]))
    story.append(Paragraph("Company guidelines on working hours, leave, remote work, code of conduct, and onboarding", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=10))

    story.append(Paragraph("1. Working Hours & Core Collaboration Hours", styles["h1"]))
    story.append(Paragraph(
        "Standard full-time business hours are 9:00 AM to 5:00 PM in your local time zone, Monday through Friday (40 hours per week). "
        "To support cross-functional collaboration while maintaining flexibility, Acme operates with core collaboration hours between <b>10:00 AM and 4:00 PM</b> local time. "
        "Employees are expected to be available for meetings and synchronous communications during these core hours. Flexible working schedules outside of core hours may be arranged with manager approval.",
        styles["body"]
    ))

    story.append(Paragraph("2. Attendance & Notification of Absence", styles["h1"]))
    story.append(Paragraph(
        "Punctuality and consistent attendance are expected. If you will be unexpectedly late or unable to work due to illness or emergency, notify your direct manager and log your absence in the HR portal prior to your scheduled start time, or as soon as reasonably practicable.",
        styles["body"]
    ))

    story.append(Paragraph("3. Paid Time Off (PTO) & Leave Policy", styles["h1"]))
    story.append(Paragraph(
        "Acme provides a comprehensive paid time off program to support employee well-being and work-life balance:",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Vacation Days:</b> Full-time employees receive <b>15 days of paid vacation per year</b>, accrued monthly at a rate of 1.25 days per month worked. Up to 5 unused vacation days may roll over into the next calendar year.", styles["bullet"]))
    story.append(Paragraph("• <b>Sick Leave:</b> Employees receive <b>10 paid sick days per year</b>, front-loaded on January 1 (or prorated upon hire date). Sick leave covers personal illness, medical appointments, and caring for immediate family members.", styles["bullet"]))
    story.append(Paragraph("• <b>Paid Holidays:</b> Acme observes <b>11 standard paid company holidays</b> each year (New Year's Day, MLK Day, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving Day & Day After, Christmas Eve, Christmas Day, and 1 Floating Holiday).", styles["bullet"]))
    story.append(Paragraph("• <b>Parental Leave:</b> Up to <b>12 weeks of 100% fully paid parental leave</b> for all new parents following birth, adoption, or foster placement, eligible after 6 months of continuous service.", styles["bullet"]))
    story.append(Paragraph("• <b>Bereavement Leave:</b> Up to 5 consecutive paid days off for the loss of an immediate family member.", styles["bullet"]))

    story.append(PageBreak())

    # PAGE 2: Remote Work, Code of Conduct & Onboarding Checklist
    story.append(Paragraph("4. Remote Work & Hybrid Workplace Policy", styles["h1"]))
    story.append(Paragraph(
        "Acme operates under a hybrid workplace policy designed for balance and collaboration:",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Hybrid Schedule:</b> Standard employees work <b>2 days in office and 3 days remote</b> per week. Designated in-office anchor days are determined by individual department leaders.", styles["bullet"]))
    story.append(Paragraph("• <b>Home Office Reimbursement Stipend:</b> New full-time employees are eligible for a one-time <b>$500 home office stipend</b> to purchase ergonomic monitors, chairs, desks, and peripheral accessories. Submit receipts via the expense portal within 60 days of hire.", styles["bullet"]))
    story.append(Paragraph("• <b>Internet Subsidy:</b> Acme provides a monthly recurring stipend of $50 towards home internet bills.", styles["bullet"]))

    story.append(Paragraph("5. Code of Conduct & Workplace Standards", styles["h1"]))
    story.append(Paragraph(
        "Acme is committed to fostering an inclusive, respectful, and safe work environment. Key principles include:",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Anti-Harassment & Non-Discrimination:</b> Zero tolerance for any form of harassment, discrimination, or retaliation based on race, gender, sexual orientation, disability, age, or religion.", styles["bullet"]))
    story.append(Paragraph("• <b>Confidentiality:</b> Employees must safeguard all proprietary corporate data, customer records, financial figures, and intellectual property.", styles["bullet"]))
    story.append(Paragraph("• <b>Conflicts of Interest:</b> Employees must disclose secondary employment or commercial interests that could conflict with their duties at Acme.", styles["bullet"]))

    story.append(Paragraph("6. Onboarding Checklist: First Day and Week 1", styles["h1"]))
    story.append(Paragraph(
        "To ensure a seamless transition, complete the following onboarding tasks:",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Before Your First Day:</b> Complete electronic I-9 employment verification, sign offer letter, and submit direct deposit banking details.", styles["bullet"]))
    story.append(Paragraph("• <b>First Day:</b> Boot laptop, set up Okta MFA, configure corporate email, join Slack #general, and meet your onboarding buddy.", styles["bullet"]))
    story.append(Paragraph("• <b>First Week:</b> Complete mandatory 30-minute Security Awareness Training, enroll in benefits (within 30 days), and complete 1-on-1 introductory meetings with your manager.", styles["bullet"]))

    story.append(Spacer(1, 10))
    story.append(create_callout_box("<b>HR People Team Contact:</b> For policy questions, leave requests, or workplace concerns, email hr-people@company.com.", styles))

    doc.build(story, canvasmaker=NumberedCanvas)


def build_security_policy(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=54
    )
    styles = get_styles()
    story = []

    # PAGE 1: MFA, Passwords, Phishing
    story.append(Paragraph("Corporate Information Security Policy", styles["title"]))
    story.append(Paragraph("Mandatory standards for authentication, credentials, data security, and incident response", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=10))

    story.append(Paragraph("1. Multi-Factor Authentication (MFA) Standards", styles["h1"]))
    story.append(Paragraph(
        "MFA is strictly mandatory for all employees and contractors accessing any Acme system, application, or network resource. "
        "SMS-based text message verification and unencrypted email codes are prohibited due to SIM-swapping and interception risks. "
        "Only app-based authenticator push notifications (Okta Verify, Google Authenticator) and FIDO2/WebAuthn hardware security keys (YubiKey) are authorized authentication methods.",
        styles["body"]
    ))

    story.append(Paragraph("2. Password Security Policy", styles["h1"]))
    story.append(Paragraph(
        "Corporate accounts must maintain high password entropy and adhere to the following standards:",
        styles["body"]
    ))
    story.append(Paragraph("• Passwords must be at least <b>14 characters in length</b> and include uppercase, lowercase, numeric, and special characters.", styles["bullet"]))
    story.append(Paragraph("• Passwords expire automatically every <b>90 days</b>. Reusing any of the last 6 previous passwords is prohibited.", styles["bullet"]))
    story.append(Paragraph("• Writing down passwords, sharing credentials with colleagues, or saving passwords in unencrypted files or web browsers is a critical security violation.", styles["bullet"]))
    story.append(Paragraph("• All employees must utilize the company-issued <b>1Password</b> enterprise password vault for storing unique credentials.", styles["bullet"]))

    story.append(Paragraph("3. Phishing Awareness & Mandatory Security Training", styles["h1"]))
    story.append(Paragraph(
        "Cyber threats and email phishing are the primary vectors for corporate attacks. All employees must comply with the following training and reporting rules:",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Mandatory Training:</b> All new hires must complete the 30-minute <b>Security Awareness Training</b> course within their first 14 days of employment.", styles["bullet"]))
    story.append(Paragraph("• <b>Phishing Simulations:</b> The Security team conducts periodic, unannounced simulated phishing tests. Employees who fail simulations are required to take remedial refresher training.", styles["bullet"]))
    story.append(Paragraph("• <b>Reporting Suspicious Emails:</b> Never click links or download attachments in unexpected emails. Report suspicious messages immediately using the 'Report Phishing' button in Outlook / Gmail or forward to phishing@company.com.", styles["bullet"]))

    story.append(PageBreak())

    # PAGE 2: Device Security, Incident Reporting
    story.append(Paragraph("4. Device Security & Workstation Hygiene", styles["h1"]))
    story.append(Paragraph(
        "Employees are responsible for securing company-issued laptops, phones, and devices at all times:",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Automatic Screen Lock:</b> Workstations must automatically lock after <b>5 minutes of inactivity</b>. Lock your screen manually (Cmd+Ctrl+Q on macOS, Win+L on Windows) whenever leaving your desk.", styles["bullet"]))
    story.append(Paragraph("• <b>Removable Media Ban:</b> Connecting personal USB flash drives, external hard drives, or unauthorized peripheral storage devices to company laptops is blocked and strictly prohibited.", styles["bullet"]))
    story.append(Paragraph("• <b>Public Wi-Fi:</b> When working from coffee shops, airports, or public venues, connecting via corporate VPN is mandatory before transmitting any work data.", styles["bullet"]))
    story.append(Paragraph("• <b>Clean Desk Policy:</b> Sensitive documents containing employee or customer data must be shredded or stored in locked cabinets when unattended.", styles["bullet"]))

    story.append(Paragraph("5. Reporting Security Incidents & Lost Devices", styles["h1"]))
    story.append(Paragraph(
        "Any suspected security breach, unauthorized access, malware detection, lost laptop, or compromised credential must be reported immediately (within 1 hour of discovery). "
        "Prompt reporting allows the Security Operations Center (SOC) to isolate compromised assets and prevent data exfiltration.",
        styles["body"]
    ))
    story.append(Paragraph("• <b>Security Incident Email:</b> security@company.com", styles["bullet"]))
    story.append(Paragraph("• <b>24/7 Urgent SOC Hotline:</b> 1-800-555-0199 (Ext 4)", styles["bullet"]))
    story.append(Paragraph("• <b>Slack Security Channel:</b> #security-incidents", styles["bullet"]))

    story.append(Spacer(1, 10))
    story.append(create_callout_box("<b>Security Rule #1:</b> Acme IT or Security personnel will NEVER ask you for your password or MFA verification code under any circumstances.", styles))

    doc.build(story, canvasmaker=NumberedCanvas)


def generate_all_mock_documents():
    """Generate all mock HR and IT onboarding PDF documents."""
    data_dir = Config.DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    docs = {
        "benefits_faq.pdf": build_benefits_faq,
        "it_setup.pdf": build_it_setup_guide,
        "employee_handbook.pdf": build_employee_handbook,
        "security_policy.pdf": build_security_policy,
    }

    print(f"Generating mock HR documents in {data_dir}...")
    for filename, builder in docs.items():
        filepath = data_dir / filename
        builder(filepath)
        print(f"  [OK] Generated: {filepath.name} ({filepath.stat().st_size} bytes)")

if __name__ == "__main__":
    generate_all_mock_documents()
