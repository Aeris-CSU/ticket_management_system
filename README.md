Members: <br>
Baccay, John Edison <br>
Morgado, Roan Carmelo <br>
Tabio, Mike Justine <br>
Tattao, Beatriz Karla

# Backend Development: Before and After Summary

Project: Help Desk Ticket Management System – RDC Technology Solutions, Inc.

This documentation summarizes the backend improvements from the original implementation (`fced3f5`), through the initial modifications (`ce193bc`), to the current implementation (`49f7c68`).

## 1. Backend Changes Summary

| Component                  | Before Implementation                                                                                                          | After Implementation (Current)                                                                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Authentication             | JWT login existed, but administrator registration was publicly accessible.                                                     | Secure JWT authentication with role-based registration. Only administrators can register technicians; public administrator registration was removed. |
| User Roles and Permissions | Role restrictions existed but did not consistently enforce ticket ownership and assignment access.                             | Improved role-based access control (RBAC) for administrators, customers, and technicians.                                                            |
| Customer Management        | Customer registration and CRUD operations existed, with incomplete validation and ownership protection.                        | Secure registration, duplicate username validation, profile access restrictions, and protected customer records.                                     |
| Technician Management      | Technician profiles existed, but availability was unrestricted text and some detail endpoints had errors.                      | Controlled availability (`AVAILABLE`/`UNAVAILABLE`), corrected endpoints, and administrator-managed technician registration.                         |
| Ticket Creation            | Customers and administrators could create tickets, but ownership and status validation were limited.                           | Tickets automatically start as `OPEN`, with validated customer ownership and restricted creation permissions.                                        |
| Ticket Visibility          | Administrators and technicians could view all tickets; customers could not access their tickets through standard ticket views. | Administrators see all tickets, customers see their own, and technicians see only currently assigned tickets.                                        |
| Ticket Status Management   | Status was unrestricted text, without a dedicated endpoint or enforced workflow.                                               | Dedicated status endpoint with controlled transitions: `OPEN → ASSIGNED → ONGOING → RESOLVED`, including cancellation rules.                         |
| Ticket Assignment          | Assignment creation lacked sufficient validation and did not automatically update ticket status.                               | Only administrators can assign technicians. Assignments validate availability and automatically update ticket status.                                |
| Ticket Reassignment        | No structured reassignment process or active-assignment tracking.                                                              | Administrators can reassign technicians while preserving previous assignment records.                                                                |
| Assignment History         | Assignments did not track active versus historical records.                                                                    | Added `is_active` and database constraints to maintain one active assignment per ticket while preserving history.                                    |
| Data Validation            | Serializers exposed broad model fields and had limited workflow validation.                                                    | Improved serializers validate user inputs, status changes, duplicate records, and assignment restrictions.                                           |
| API Endpoints              | Several CRUD operations were incomplete, and some missing-record errors were not properly handled.                             | Improved REST API endpoints, dedicated status updates, corrected deletion behavior, and better error responses.                                      |
| Data Protection            | Records could be deleted without consistently protecting related ticket and assignment history.                                | Deletion restrictions protect customers, technicians, and tickets with related historical records.                                                   |
| Database Operations        | Related operations lacked consistent transaction protection.                                                                   | Database transactions, row locks, and uniqueness constraints improve data consistency.                                                               |
| CORS and Configuration     | CORS support was not enabled, and configuration relied on less flexible settings.                                              | Configurable CORS and environment-based security, database, and deployment settings.                                                                 |
| Backend Testing            | Dedicated regression coverage was limited or missing.                                                                          | Added backend test files covering authentication, tickets, assignments, and technicians.                                                             |

## 2. Explanation of Backend Improvements

The backend of the Help Desk Ticket Management System was improved to provide a more secure, organized, and reliable ticket management process. Initially, the system supported basic CRUD operations, user authentication, and ticket assignments, but it had limitations in access control, data validation, and ticket status management. The updated implementation introduced stricter role-based permissions, allowing customers to manage their own ticket submissions, technicians to work only on their assigned tickets, and administrators to control technician assignments and overall ticket operations. A structured ticket workflow was implemented to ensure that tickets follow valid status transitions, while assignment tracking was enhanced to support reassignment and preserve historical records. Additionally, database transactions, validation rules, protected deletion operations, and improved API endpoints were added to maintain data integrity and strengthen security. These changes established a more stable backend foundation for integration with the Vue.js frontend.

## 3. Overall Development Outcome

| Category             | Improvement Achieved                                                                              |
| -------------------- | ------------------------------------------------------------------------------------------------- |
| Security             | Stronger authentication, role-based permissions, and restricted access to records.                |
| Functionality        | Complete ticket lifecycle with controlled assignment, reassignment, resolution, and cancellation. |
| Reliability          | Improved validation, database consistency, and error handling.                                    |
| Maintainability      | Better-organized API behavior and configuration management.                                       |
| Frontend Integration | More consistent API responses and configurable CORS for Vue.js integration.                       |

Conclusion: The backend evolved from a basic CRUD-based ticket management application into a more structured, role-controlled help desk system. The improvements strengthen security, ticket workflow management, assignment tracking, and database integrity, providing a foundation for frontend integration and further system development.

