# Recruitment Business Logic (`hr_recruitment_custom`)

The `hr_recruitment_custom` module enhances Odoo's default recruitment application to streamline applicant tracking, interview scheduling, and hiring processes tailored for our specific organizational structure.

## 1. Applicant Tracking and Pipeline
- **Customized Job Positions**: Job listings are categorized and linked directly to internal departments. Each job acts as a pipeline to funnel applications.
- **Application Sourcing**: Applicants are generated either manually by HR personnel or automatically via integrated email aliases (e.g., `jobs@company.com`) or web forms.
- **Pipeline Stages**: The recruitment workflow is divided into clear, manageable stages (e.g., Initial Qualification $\rightarrow$ First Interview $\rightarrow$ Second Interview $\rightarrow$ Contract Proposal $\rightarrow$ Hired/Refused). These stages represent the candidate's progression.

## 2. Evaluation and Interviews
- **Collaborative Review**: Hiring managers and assigned recruiters can review applicant records, log internal notes, and attach resumes or portfolios directly to the applicant's profile.
- **Interview Scheduling**: Integration with Odoo's calendar allows recruiters to schedule meetings with candidates directly from the applicant view, automatically notifying all required attendees.
- **Rating system**: Feedback mechanisms allow interviewers to rate applicants.

## 3. Hiring and Onboarding
- **Status Flagging**: Candidates are classified by their application status (Ongoing, Hired, Refused, Archived). Refusal reasons must be logged to maintain database cleanliness and provide historical data.
- **Direct Employee Creation**: Once a candidate accepts an offer and is moved to the "Hired" stage, HR can use the `Create Employee` functionality. This action automatically transfers all collected personal data (Name, Email, Phone, Department) into a new `hr.employee` profile, eliminating duplicate data entry.

## 4. UI/UX and Access Enhancements
- Includes customized Search, Kanban, and Form views to ensure that Recruiter and Manager roles only see the candidate data relevant to their permissions.
- Prevents lower-tier users from altering pipeline configuration or deleting active prospects.

---

## 5. Important Notes & System Automations

**Prerequisites for Users**:
- Ensure email aliases are properly configured on the server end if the company wishes to capture applicant generation automatically from inbound generic emails.

**What the System Does Automatically**:
- **Applicant to Employee Conversion**: When clicking the `Create Employee` button on a hired candidate's profile, the system skips all manual drafting. It automatically instantiates a new `hr.employee` record mapping over the applicant's name, private phone, email, and proposed department. If documents (resumes, ID scans) were attached to the applicant profile, they remain linked to the history of the newly onboarded employee.
- **Stage Progression Dates**: Odoo natively catches when you drag a candidate to a new stage in Kanban, automatically updating variables like `date_last_stage_update` giving managers accurate analytics on how active each recruitment pipeline is.
