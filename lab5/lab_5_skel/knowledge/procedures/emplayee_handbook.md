# Internal Corporate Handbook

## NovaCore Technologies - Employee Operations and Engineering Guide

### Version 4.2 (Fictional Internal Documentation)

***

# Employee Onboarding

## Overview

The employee onboarding process at NovaCore Technologies is designed to ensure that every new team member becomes productive, secure, and aligned with company standards as quickly as possible. The onboarding experience starts after the employment agreement has been signed and continues throughout the employee's first ninety days.

The onboarding program is coordinated jointly by Human Resources, Information Technology Operations, Security Engineering, and the employee's direct manager. Each department has clearly defined responsibilities to ensure a predictable and consistent employee experience.

The standard onboarding timeline consists of the following phases:

* Pre-boarding preparation
* First day provisioning
* First week access verification
* First month productivity milestones
* Ninety-day integration review

The company maintains a goal that every employee should have access to all required tools before 10:00 AM on their first working day.

***

## Laptop Provisioning and Access

### Hardware Assignment

Every employee receives a company-managed laptop based on their role and responsibilities.

Software Engineers typically receive:

* Lenovo ThinkPad X1 Carbon
* Dell XPS Developer Edition
* Apple MacBook Pro depending on project requirements

Quality Assurance Engineers typically receive:

* Lenovo ThinkPad T-series
* MacBook Air
* Dell Latitude professional models

DevOps Engineers and Platform Engineers may receive laptops with increased memory capacity to support virtualization workloads and infrastructure tooling.

The standard laptop configuration includes:

* Minimum 32 GB RAM
* SSD storage
* Full disk encryption enabled
* Company endpoint protection software
* Remote management agent
* Asset inventory tracking software

### Laptop Collection Process

Before a start date, the IT Operations team prepares a device package including:

* Assigned laptop
* Charging equipment
* Security documentation
* Hardware asset identification record

Employees working remotely receive equipment through approved courier services. Upon delivery, employees must confirm hardware receipt through the Employee Services Portal.

### First Login Procedure

On the first login:

1. Connect to a trusted internet connection.
2. Authenticate using temporary onboarding credentials.
3. Change the temporary password immediately.
4. Register multi-factor authentication.
5. Allow the device to complete management synchronization.
6. Reboot the device when prompted.

The synchronization process installs essential software automatically and may require up to thirty minutes depending on network conditions.

### Device Compliance Checks

Before access to sensitive systems is granted, devices must pass automated compliance validation.

Compliance requirements include:

* Updated operating system
* Active endpoint protection
* Disk encryption enabled
* Firewall enabled
* Device certificate installed
* Current security policies applied

Devices that fail compliance checks are automatically restricted from accessing internal resources.

***

## Account Configuration

### Corporate Identity Account

Every employee receives a corporate identity account based on the following convention:

<firstname.lastname@novacore.example>

The identity account serves as the primary authentication source for:

* Email
* Collaboration platforms
* Internal applications
* Cloud services
* VPN access
* Knowledge bases

### Initial Password Requirements

Temporary passwords are generated automatically by the Identity Management Platform.

Users must create a permanent password that satisfies the following requirements:

* Minimum sixteen characters
* One uppercase character
* One lowercase character
* One number
* One special character
* No reuse of previous twelve passwords

Employees are encouraged to use passphrases rather than short complex passwords.

Example of acceptable passphrase patterns:

* Multiple unrelated words
* Memorable project-independent phrases
* Password manager generated credentials

### Email Setup

The company uses a cloud-hosted enterprise email platform.

Required email configuration steps include:

* Accepting acceptable use policy
* Configuring email signature
* Reviewing mailbox retention guidelines
* Enabling mobile device authentication if applicable

Employees should review onboarding communications stored in the Welcome folder automatically created in their mailbox.

### Messaging and Collaboration Services

New employees receive access to:

* Corporate chat platform
* Video conferencing systems
* Team collaboration workspaces
* Internal communities
* Engineering discussion channels

Employees are expected to update profile information within the first week.

This includes:

* Profile photo
* Preferred name
* Department
* Manager
* Location
* Emergency contact verification

***

## VPN Access

### Purpose of VPN Access

The Virtual Private Network (VPN) service provides secure connectivity between remote users and company infrastructure.

VPN access is mandatory when:

* Accessing internal web applications
* Connecting to engineering environments
* Accessing restricted repositories
* Managing infrastructure resources
* Working from public networks

### VPN Enrollment Procedure

New employees receive VPN eligibility based on role assignments.

The enrollment process includes:

1. Device compliance verification
2. Security awareness training completion
3. MFA registration
4. Manager approval confirmation
5. Automated access provisioning

### Connection Process

To connect:

1. Launch the approved VPN client.
2. Authenticate using corporate credentials.
3. Approve identity verification request.
4. Wait for connection confirmation.
5. Verify assigned network profile.

VPN profiles are assigned according to team memberships.

Examples include:

* Engineering Standard
* Quality Assurance
* Platform Operations
* Customer Support
* Security Operations

### VPN Usage Expectations

Employees should disconnect from VPN when not actively performing company work.

The VPN service logs:

* Connection times
* Device information
* Authentication events
* Geographic region
* Security anomalies

Content inspection is limited to corporate traffic necessary for operational security monitoring.

***

## GitHub Access

### GitHub Enterprise Environment

NovaCore Technologies uses an internally managed GitHub Enterprise environment known as NovaHub.

NovaHub hosts:

* Source code repositories
* Infrastructure definitions
* Documentation
* Deployment configurations
* Internal developer tools

### Access Request Workflow

GitHub access is not granted automatically.

The onboarding workflow includes:

1. Manager sponsorship
2. Team assignment validation
3. Security training completion
4. GitHub access approval
5. Repository assignment

Most employees receive access within four working hours after onboarding completion.

### Repository Permissions

Access follows the principle of least privilege.

Permission levels include:

#### Read

Users can:

* View code
* Clone repositories
* Review documentation

#### Write

Users can:

* Push changes
* Create branches
* Submit pull requests

#### Maintain

Users can:

* Manage branches
* Configure repository settings
* Archive repositories

#### Admin

Reserved for platform owners and authorized administrators.

### SSH Key Registration

Employees must register SSH keys before pushing code.

Requirements include:

* Minimum RSA 4096-bit or modern equivalent
* Unique keys per device
* No shared credentials
* Immediate revocation upon device loss

### GitHub Best Practices

All users should:

* Protect personal access tokens
* Enable MFA
* Review repository permissions quarterly
* Report unusual activity immediately

Examples of suspicious activity include:

* Unexpected repository invitations
* Unknown pull requests
* Unauthorized branch creation
* Failed login attempts from unfamiliar locations

***

## First Week Expectations

### Day One Objectives

By the end of the first working day, employees should:

* Successfully log in to all systems
* Access company email
* Join team communication channels
* Connect through VPN
* Access assigned repositories
* Complete mandatory courses

### Week One Objectives

During the first week, employees are expected to:

* Meet their manager
* Meet team members
* Understand project context
* Review engineering documentation
* Complete security awareness training
* Complete compliance acknowledgement

Employees should maintain a personal onboarding checklist and review progress with their manager during the end-of-week check-in.

### Required Learning Modules

Mandatory learning includes:

* Information Security Fundamentals
* Data Protection Awareness
* Secure Software Development
* Incident Reporting Procedures
* Workplace Conduct Policies
* Remote Work Guidelines

Each module concludes with an assessment.

Minimum passing score is 85%.

***

## Ninety-Day Integration Program

### First Month

The first month focuses on orientation and productivity.

Employees should:

* Complete onboarding tasks
* Participate in team ceremonies
* Contribute minor improvements
* Review architecture documentation
* Learn organizational processes

### Second Month

Employees are expected to:

* Deliver independently scoped work
* Participate actively in discussions
* Review peer contributions
* Build domain expertise

### Third Month

Employees should:

* Demonstrate operational independence
* Understand escalation paths
* Participate in planning activities
* Contribute process improvements

Managers conduct a formal integration review at approximately ninety days.

Review criteria include:

* Technical performance
* Collaboration
* Security compliance
* Communication effectiveness
* Learning progress

Successful completion transitions the employee from onboarding status to standard operational status.

***

# Password Reset Procedure

## Purpose

The Password Reset Procedure defines the approved method for restoring access to company systems while maintaining security controls and regulatory compliance requirements.

Password-related incidents represent one of the most frequently reported support requests across the organization. A standardized process ensures consistency, security, and traceability.

The procedure applies to:

* Full-time employees
* Contractors
* Interns
* Third-party support personnel with approved accounts

***

## Common Password Reset Scenarios

Password resets are typically required when:

* A password has been forgotten.
* An account has become locked.
* A password has expired.
* Suspicious activity has been detected.
* A security event requires credential rotation.
* An employee returns from extended leave.

The remaining sections of this procedure define the required actions for each scenario.

***

## Self-Service Password Reset

### Eligibility

Employees can use the Self-Service Password Reset Portal if they previously registered:

* Mobile authentication
* Recovery email
* MFA device

### Reset Process

Step 1: Visit the Identity Portal.

Step 2: Select "Forgot Password."

Step 3: Enter corporate email address.

Step 4: Complete identity verification.

Step 5: Choose a new password.

Step 6: Confirm successful password update.

Step 7: Re-authenticate on all company devices.

### Post-Reset Activities

After a successful reset, employees should:

* Update password manager records
* Reconnect mobile applications
* Verify MFA functionality
* Review account activity history

Users should immediately report unfamiliar activity discovered during account review.

***

## Account Lockout Recovery

Repeated authentication failures may trigger automatic account lockout protections.

Default thresholds include:

* Ten failed login attempts within fifteen minutes
* Excessive API authentication failures
* Automated attack detection events

Employees should avoid repeated login attempts after a lockout notification has been received.

Instead, they should follow the approved recovery workflow.

***

# Password Reset Procedure (Continued)

## Support-Assisted Password Reset

### When Support Intervention Is Required

Employees must contact the Service Desk when:

* MFA devices are unavailable
* Recovery methods are inaccessible
* The account is disabled
* Identity verification fails
* The employee suspects account compromise

### Identity Verification Requirements

Before a password reset is performed, support personnel must verify the employee's identity.

Approved verification methods include:

* Employee ID validation
* Manager confirmation
* Registered phone verification
* Video identification session
* Security challenge questions

Support representatives may not bypass identity verification procedures under any circumstances.

### Emergency Access Recovery

In rare situations involving business-critical responsibilities, expedited credential recovery may be authorized.

Examples include:

* Production incident response
* Critical customer outage management
* Security containment activities
* Regulatory reporting deadlines

Emergency recovery events are reviewed by Security Operations within one business day.

***

## Security Rules for Password Management

### Password Construction Guidelines

Employees should avoid:

* Personal names
* Pet names
* Birth dates
* Company names
* Project names
* Sequential numbers
* Keyboard patterns

Weak examples:

* Company2026
* Password123
* Summer2026
* Welcome123

Strong passwords generally contain unrelated words and sufficient length.

### Password Storage Requirements

Passwords must never be:

* Stored in plain text documents
* Shared through chat platforms
* Sent through email
* Stored in spreadsheets
* Printed on paper attached to devices

Employees are encouraged to use the approved enterprise password manager.

### Credential Sharing Policy

Sharing credentials is strictly prohibited.

Each action performed within company systems must remain attributable to a specific individual.

Violations may result in:

* Security investigations
* Access suspension
* Disciplinary action
* Compliance reviews

### Suspected Credential Compromise

Employees who suspect credential exposure must:

1. Change the password immediately.
2. Notify Security Operations.
3. Review recent account activity.
4. Log out from active sessions.
5. Re-register MFA if necessary.

Examples of potential compromise indicators include:

* Unexpected MFA requests
* Login alerts from unfamiliar regions
* Unauthorized password change notifications
* Unrecognized repository activity

***

## Service Desk Contact Information

### Primary Support Channels

The Internal Service Desk provides support through:

* Support Portal
* Corporate Chat Support Channel
* Email Ticket Submission
* Emergency Hotline

### Standard Operating Hours

Support Coverage:

* Monday through Friday
* 07:00 to 19:00 local time

### Extended Coverage

Critical incidents affecting authentication services receive 24/7 operational support.

The Identity Management Team maintains on-call rotations for severe outages impacting employee productivity or customer services.

***

# Incident Management

## Purpose

Incident Management provides a structured process for identifying, categorizing, prioritizing, investigating, resolving, and reviewing events that disrupt normal business operations.

The objective is to restore services quickly while minimizing operational and customer impact.

Incident Management applies to:

* Software platforms
* Infrastructure services
* Internal applications
* Customer-facing systems
* Security events
* Third-party service dependencies

***

## Incident Definition

An incident is any unplanned interruption or degradation of a service.

Examples include:

* Application crashes
* API failures
* Database outages
* Authentication disruptions
* Cloud infrastructure failures
* Monitoring system failures
* Security alerts requiring investigation

Not every defect is considered an incident.

A bug discovered in a development environment without operational impact is typically handled through normal engineering processes rather than incident response procedures.

***

## Incident Classification

### Infrastructure Incidents

Infrastructure incidents affect foundational technology components.

Examples:

* Cloud network disruptions
* Virtual machine failures
* Storage outages
* DNS failures
* VPN disruptions

### Application Incidents

Application incidents affect software functionality.

Examples:

* Service crashes
* API latency increases
* Deployment failures
* Broken user workflows

### Security Incidents

Security incidents involve potential compromise of confidentiality, integrity, or availability.

Examples:

* Malware detection
* Suspicious authentication activity
* Data exposure
* Unauthorized access attempts

### Third-Party Incidents

Third-party incidents originate from vendors or external providers.

Examples:

* SaaS outages
* Cloud service disruptions
* Authentication provider failures
* Payment gateway instability

***

## Incident Priority Levels

### Priority 1 (Critical)

Characteristics:

* Complete service outage
* Significant customer impact
* Major revenue risk
* Security event with active exploitation

Examples:

* Production platform unavailable globally
* Customer authentication unavailable
* Critical database unavailable

Expected response time:

* Immediate response
* Incident command established within fifteen minutes

### Priority 2 (High)

Characteristics:

* Severe degradation
* Limited workaround availability
* Multiple customers affected

Examples:

* API response times significantly degraded
* Partial outage of major functionality

Expected response time:

* Response within thirty minutes

### Priority 3 (Medium)

Characteristics:

* Moderate operational impact
* Workaround exists

Examples:

* Reporting functionality unavailable
* Non-essential workflow degradation

Expected response time:

* Response within four hours

### Priority 4 (Low)

Characteristics:

* Minor inconvenience
* Limited impact

Examples:

* Cosmetic defects
* Documentation issues
* Non-critical service warnings

Expected response time:

* Response within one business day

***

## Incident Lifecycle

### Identification

Incidents may be identified through:

* Monitoring alerts
* Customer reports
* Employee reports
* Security tooling
* Automated anomaly detection

### Logging

Every incident receives:

* Unique identifier
* Creation timestamp
* Reporter information
* Affected service details
* Initial business impact assessment

### Assessment

The Incident Coordinator evaluates:

* Scope of impact
* Number of affected users
* Technical severity
* Business consequences

### Response

Response activities may include:

* Traffic rerouting
* Service rollback
* Infrastructure failover
* Emergency configuration changes
* Vendor escalation

### Resolution

The resolution phase focuses on restoring normal service operation.

Temporary workarounds may be used when full remediation requires longer-term engineering work.

### Closure

Before closure:

* Service stability must be confirmed.
* Stakeholders must be notified.
* Root cause investigation requirements must be assessed.

***

## Escalation Process

### Functional Escalation

Functional escalation occurs when additional expertise is required.

Examples:

* Escalating application issues to engineering
* Escalating cloud failures to platform teams
* Escalating database issues to database administrators

### Hierarchical Escalation

Management escalation occurs when:

* Resolution exceeds SLA targets
* Business impact increases
* Customers require executive communication

Management levels may include:

* Engineering Manager
* Director
* Vice President
* Executive Leadership Team

***

## Incident Communication

### Internal Communication

Updates should be provided at agreed intervals.

Recommended frequencies:

* Priority 1: every 30 minutes
* Priority 2: every 60 minutes
* Priority 3: every 4 hours
* Priority 4: daily

### Customer Communication

Customer updates should contain:

* Current status
* Affected functionality
* Known workarounds
* Expected next update time

Communications should avoid speculation and unverified technical assumptions.

***

## Service Level Agreements (SLA)

### Priority 1

Target response:

* 15 minutes

Target restoration:

* 4 hours

### Priority 2

Target response:

* 30 minutes

Target restoration:

* 8 hours

### Priority 3

Target response:

* 4 hours

Target restoration:

* 3 business days

### Priority 4

Target response:

* 1 business day

Target restoration:

* Best effort prioritization

***

## Post-Incident Review

Priority 1 and Priority 2 incidents require formal review.

Topics include:

* Timeline reconstruction
* Root cause analysis
* Contributing factors
* Detection effectiveness
* Communication quality
* Preventive actions

Deliverables include:

* Incident summary
* Action item register
* Executive overview
* Ownership assignments

***

# Vacation Policy

## Purpose

The Vacation Policy establishes guidelines for requesting, approving, scheduling, and tracking employee vacation leave.

The company encourages employees to take regular breaks to support long-term well-being, productivity, and professional sustainability.

***

## Annual Vacation Entitlement

### Standard Allocation

Full-time employees receive:

* 25 paid vacation days per calendar year

Vacation balances are visible through the Employee Services Portal.

### Senior Employees

Employees with five years of continuous service receive:

* 28 paid vacation days annually

Employees with ten years of continuous service receive:

* 30 paid vacation days annually

### Part-Time Employees

Vacation entitlement is calculated proportionally based on contracted working hours.

***

## Vacation Planning Expectations

Employees are encouraged to schedule vacations in advance.

Recommended notice periods:

* One day leave: at least three business days
* One week leave: at least two weeks
* Multiple weeks leave: at least one month

Advance planning improves team coverage and project predictability.

***

## Vacation Approval Procedure

### Employee Responsibilities

Employees must:

1. Submit request through HR portal.
2. Select requested dates.
3. Verify sufficient balance.
4. Notify project stakeholders when required.

### Manager Responsibilities

Managers review:

* Team coverage
* Project commitments
* Business priorities
* Existing approved leave

Managers should approve or reject requests promptly.

Target review time is three business days.

***

## Peak Vacation Periods

Certain periods experience elevated leave demand.

Examples include:

* Summer months
* Winter holidays
* Regional public holidays

Managers may coordinate schedules to ensure adequate operational coverage.

When multiple employees request identical periods, consideration may include:

* Submission date
* Business requirements
* Historical vacation patterns
* Team staffing levels

***

## Special Vacation Rules

### Carryover Policy

Employees may carry over:

* Up to five unused vacation days

Carried-over days must be used by the end of the first quarter of the following year.

### Extended Leave

Requests exceeding three consecutive weeks require:

* Additional management review
* Project transition planning
* Knowledge transfer activities

### Mandatory Time Off

Employees in sensitive operational positions may be required to take consecutive vacation periods to support internal control processes and fraud prevention measures.

***

# Expense Reimbursement

## Purpose

The Expense Reimbursement Program allows employees to recover approved business-related expenses incurred while performing authorized company activities.

Only legitimate business expenses are eligible for reimbursement.

***

## Eligible Expenses

Common reimbursable expenses include:

* Business travel
* Hotel accommodation
* Client meetings
* Conference registration
* Approved training programs
* Local transportation
* Parking expenses
* Business meals

All expenses must have a legitimate business purpose.

### Travel Expenses

Approved travel expenses include:

* Economy airfare
* Train transportation
* Airport transfers
* Taxi services
* Rideshare services

Employees are expected to select cost-effective options when available.

### Education and Training

Training reimbursement may include:

* Professional certifications
* Technical conferences
* Industry workshops
* Approved online learning programs

Manager approval must generally be obtained before registration.

***
