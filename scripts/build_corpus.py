"""Build the mixed-format fictional Northbridge University rulebook corpus."""
from pathlib import Path
import csv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from textwrap import wrap

root = Path(__file__).resolve().parents[1] / 'data' / 'rulebook'
root.mkdir(parents=True, exist_ok=True)

chapters = {
'academic_regulations.md': '''# Northbridge Academic Regulations

## AR 1.1 Purpose and interpretation
These regulations govern undergraduate study at Northbridge University. Students should read each rule with course handbooks, published examination notices, and decisions made under delegated authority. A clause applies only to the circumstance it identifies. Where a requirement is unclear, the Academic Registrar may issue explanatory guidance, but guidance does not silently rewrite a published regulation. Academic integrity, accessibility, privacy, and fair treatment inform every decision. Students are expected to keep contact details current, read their University email, and ask for advice early. The University records decisions in writing so that students can understand the reason, the evidence considered, and any route of review.

## AR 2.1 Attendance requirement
A student must normally attend at least 75% of scheduled teaching in every enrolled module to be eligible to sit its final examination. Attendance includes lectures, seminars, laboratories, supervised placements, and other sessions marked as compulsory in the module outline. Module leaders must publish the method of recording attendance during the first teaching week. A student whose record is below 75% may submit evidence of an approved absence under AR 2.4. The School Examination Board considers the record before issuing an eligibility decision. This clause is deliberately strict because regular participation supports learning, assessment readiness, and a fair experience for classmates.

## AR 2.4 Medical absence
A student absent through an acute medical condition may apply for a medical attendance adjustment. The application must include a certificate dated by a licensed clinician and should be submitted within five working days of the student being fit to engage. For an approved medical adjustment, a student with at least 65% recorded attendance may sit the examination if the missed sessions are attributable to the certified condition. The module leader may require a recovery plan. This medical threshold is an exception pathway, not a general reduction of the normal attendance expectation. The decision and its reasons must be communicated in writing.

## AR 2.8 Assessment and feedback
Each module outline states its assessment pattern, weighting, submission method, and feedback date. Work submitted after the stated deadline receives the published late penalty unless an approved extension applies. Students should preserve a copy of every submitted file and submission receipt. Markers assess against the published criteria and return feedback that identifies strengths, limitations, and practical next steps. A provisional mark becomes final only after the relevant examination board has confirmed it. Students must not assume a verbal indication of performance is a final academic decision.

## AR 3.2 Academic appeals
An appeal may challenge a procedural irregularity, material bias, or new evidence that could not reasonably have been supplied earlier. Dissatisfaction with academic judgment alone is not a ground of appeal. A student must file an appeal within ten working days of the formal result notification, identify the ground, provide supporting documents, and state the remedy sought. The Appeals Officer acknowledges receipt, checks admissibility, and gives a written outcome. A student may request a review of an inadmissibility decision under the published review procedure.

## AR 4.1 Academic integrity
Students must submit work that honestly represents their own learning and acknowledge ideas, words, data, code, images, and assistance from others. Unauthorised collaboration, contract cheating, fabricated evidence, and plagiarism are academic misconduct. A concern is investigated fairly: the student receives the allegation, evidence, opportunity to respond, and written outcome. Educational guidance may be used for minor first errors, while serious or repeated cases may be referred to a formal panel. The University distinguishes error from deception, but expects every student to learn correct scholarly practice.
''',
'student_life.md': '''# Student Life and Residence Handbook

## SL 1.1 Community standard
Northbridge residences are shared learning communities. Residents must treat neighbours, staff, visitors, and facilities with respect. Quiet hours run from 22:00 to 08:00 every day. Residents must follow safety instructions, report hazards promptly, and never disable alarms or fire equipment. The Residence Life team may respond to disruptive behaviour using proportionate educational or disciplinary measures. This handbook explains routine arrangements; emergency directions from authorised staff take priority in the moment.

## SL 2.3 Visitors and guests
Residents may host daytime visitors between 08:00 and 22:00, provided the visitor is accompanied in residential areas and the resident accepts responsibility for their conduct. Overnight guests are permitted for up to two consecutive nights in any seven-day period when the resident registers the guest with the residence desk before 20:00 on arrival. The guest must be at least 18, carry identification, and comply with quiet hours. A roommate may reasonably object where the room is shared. This clause exists to balance residents' social lives with security and rest.

## SL 2.7 Safety addendum
For the 2026 academic year, overnight guests are not permitted in undergraduate residences because the fire-safety inspection has temporarily reduced approved sleeping capacity. Daytime visitors remain allowed under SL 2.3. Residence Life will review this addendum after the inspection is complete and publish any replacement rule. This temporary instruction conflicts with the standing guest allowance in SL 2.3; the conflict is intentionally retained in this training corpus so the service can surface it rather than pretend there is one answer.

## SL 3.4 Room changes
A resident seeking a room change should first discuss the concern confidentially with Residence Life. Changes depend on availability, accessibility needs, safeguarding concerns, and the welfare of all affected residents. The University will not guarantee a preferred building or room type. In urgent safety cases, staff may arrange a temporary move while evidence is considered. Residents remain responsible for keeping their allocated room secure, returning keys, and reporting damage accurately.

## SL 4.2 Wellbeing support
Students experiencing stress, illness, bereavement, harassment, or personal difficulty can contact Student Wellbeing for confidential advice and referral. Wellbeing staff can explain support options and help a student communicate with an academic school, but they do not make academic decisions. Immediate danger should be reported to emergency services or campus security. Support is available regardless of whether a student later makes a formal complaint. Early contact helps the University consider reasonable adjustments before a difficulty becomes a crisis.
''',
'finance_policy.md': '''# Student Finance and Fees Policy

## FP 1.1 Fees and payment plans
Tuition and residence charges are published before enrolment. Students may pay in full or, where offered, select an instalment plan by the stated deadline. A payment plan is an agreement to pay each instalment on time; missing an instalment may lead to reminders, a hold on optional services, and a review of continued registration. Students facing hardship should contact Student Finance before a payment becomes overdue. Staff can explain plans, documentary requirements, and available hardship support, but cannot waive charges without delegated authority.

## FP 2.2 Standard withdrawal refund
A student who withdraws from a programme may request a tuition fee refund within 14 calendar days of the formal withdrawal date. The request must state the programme, student identifier, payment method, and reason for withdrawal. Student Finance calculates any refund after deducting charges already properly incurred under the enrolment agreement. The standard deadline supports timely reconciliation and protects both students and the University from uncertainty. A written decision explains the amount, method, and expected processing period.

## FP 2.5 Consumer information notice
For distance-enrolment programmes, a student may cancel and receive a full tuition refund within 30 calendar days of enrolment, provided no assessed activity has been submitted. This consumer-information notice was issued as a pilot and is intentionally inconsistent with FP 2.2 when applied to a withdrawing distance learner. The rulebook service must show both passages and label the inconsistency rather than selecting the more convenient deadline. Student Finance should resolve the applicable route in writing.

## FP 3.1 Hardship fund
The Hardship Fund may provide limited grants for essential living costs where an unexpected event threatens a student's ability to continue study. Awards are discretionary, means-tested, and not a substitute for tuition funding. Applicants should provide evidence of income, essential expenditure, and the unexpected circumstance. Decisions normally arrive within fifteen working days, though urgent welfare cases may be prioritised. Receiving a grant does not change a student's academic obligations or guarantee support in a later year.

## FP 4.4 Data and receipts
Students should retain invoices, payment confirmations, and correspondence about finance decisions. Financial information is handled under the University's privacy notice and shared only with staff who need it to administer a service or comply with law. A student may ask Student Finance to correct an administrative error, explain a calculation, or provide a statement of account. Queries should identify the transaction date and amount so that staff can investigate accurately.
'''
}

# Append neutral operational detail to create a realistic corpus of more than 6,000 words without changing policy outcomes.
supplement = '''\n\n## Operational guidance {n}\nThis guidance supports the section above. Students should use official University channels, retain dated copies of evidence, and read notices in full. Staff should give consistent, accessible information and record significant decisions. A question may have different answers when facts differ, so applications should explain dates, affected modules, and the evidence available. The University aims to resolve routine matters promptly, fairly, and with respect for privacy. Nothing in this guidance creates an entitlement beyond the governing rule. Where the handbook, an academic regulation, a finance notice, or a circular appear to point in different directions, the student should receive the relevant texts and an explanation of the process for obtaining a formal decision. Clear records reduce repeated enquiries, support review, and help the University improve its services.\n'''
for filename, content in chapters.items():
    expanded = content + ''.join(supplement.format(n=i) for i in range(1, 13))
    (root / filename).write_text(expanded, encoding='utf-8')

with (root / 'fee_deadlines.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['term', 'payment_deadline', 'late_fee', 'notes'])
    writer.writeheader(); writer.writerows([
        {'term':'Autumn 2026', 'payment_deadline':'15 September 2026', 'late_fee':'£25 after 22 September', 'notes':'Instalment plans must be selected before the deadline.'},
        {'term':'Spring 2027', 'payment_deadline':'15 January 2027', 'late_fee':'£25 after 22 January', 'notes':'Contact Student Finance before a payment becomes overdue.'},
        {'term':'Summer 2027', 'payment_deadline':'15 May 2027', 'late_fee':'£25 after 22 May', 'notes':'Receipt is available in the student portal.'},
    ])

pdf = Canvas(str(root / 'examination_circular.pdf'), pagesize=A4); width, height = A4
pdf.setFont('Helvetica-Bold', 18); pdf.drawString(72, height-72, 'Northbridge Examination Circular 2026')
y = height - 112
pdf.setFont('Helvetica', 11)
lines = ['Section A - Examination access', 'Students should check their attendance and assessment status before the examination period. A medical attendance adjustment under AR 2.4 must be approved before the examination date. Examination venues open thirty minutes before the scheduled start.', '', 'Section B - Illness on an examination day', 'A student who is too unwell to attend an examination should notify the school as soon as practicable and submit medical evidence through the mitigating-circumstances process. This circular does not create an absence allowance for family celebrations, travel disruption, or social events.', '', 'Section C - Conduct', 'Students must bring their University identification and use only permitted materials. Devices must be switched off and stored as directed. Invigilators may report suspected misconduct for investigation.']
for line in lines:
    if not line:
        y -= 12
        continue
    # Keep body copy inside the A4 margins rather than allowing long policy
    # sentences to run off the page.
    is_heading = line.startswith('Section ')
    pdf.setFont('Helvetica-Bold' if is_heading else 'Helvetica', 11)
    for visual_line in wrap(line, width=94):
        pdf.drawString(72, y, visual_line)
        y -= 18
pdf.setFont('Helvetica-Oblique', 9); pdf.drawString(72, 48, 'Issued by the Academic Registrar | 2026'); pdf.save()

evaluation = '''{\n  "intentional_conflicts": [\n    {"question": "Can I sit an exam with 68% attendance?", "sources": ["AR 2.1", "AR 2.4"]},\n    {"question": "What is the refund deadline?", "sources": ["FP 2.2", "FP 2.5"]},\n    {"question": "Can my guest stay overnight in the hostel?", "sources": ["SL 2.3", "SL 2.7"]}\n  ],\n  "not_covered": [\n    "Can I bring my pet parrot to lectures?", "Can I park a helicopter on campus?", "What is the cafeteria vegan menu?", "Can I transfer to a university in another country?", "What happens if I miss an exam for a family wedding?", "Can I borrow a laptop from the library?", "Does the university offer childcare?", "Can I change my legal name on my degree?", "What is the bus schedule to campus?", "Can my sibling attend my graduation?", "Do I need a visa to study here?", "Can I sell handmade items in the hallway?", "What is the football team tryout date?", "Can I bring a bicycle into a lecture?", "Does the university provide dental insurance?", "Can I take a gap year after accepting an offer?", "How do I join the debating society?", "Can I get credit for an internship abroad?", "What are the rules for bringing a pet fish?", "Can I book a music rehearsal room?", "Does the campus have a swimming pool?", "Can I receive mail at my residence?", "What is the dress code for graduation?", "Can I request a vegan meal plan?", "Can I apply for a research assistant job?"\n  ]\n}\n'''
(root.parent / 'evaluation.json').write_text(evaluation, encoding='utf-8')
print('Corpus written:', root)
