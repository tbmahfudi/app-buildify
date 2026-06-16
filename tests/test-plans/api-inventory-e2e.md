# Live API Inventory — app_buildify_backend

Base: http://localhost:8000  ·  Prefix: /api/v1  ·  291 operations across 23 routers

_Source: GET /api/openapi.json from the running container. Each row is one exhaustive-coverage target._

## Data Model Designer  (26 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Entities |
| POST |  | Create Entity |
| POST |  | Regenerate Entity Menus |
| DELETE |  | Delete Entity |
| GET |  | Get Entity |
| PUT |  | Update Entity |
| POST |  | Clone Entity |
| GET |  | List Fields |
| POST |  | Create Field |
| GET |  | List Deleted Fields |
| DELETE |  | Delete Field |
| PUT |  | Update Field |
| DELETE |  | Permanently Delete Field |
| POST |  | Restore Field |
| POST |  | Generate Migration |
| GET |  | List Migrations |
| GET |  | Preview Migration |
| POST |  | Publish Entity |
| POST |  | Batch Generate Entities |
| POST |  | Generate Entity From Db Object |
| GET |  | List Database Objects |
| POST |  | Execute Migration |
| POST |  | Rollback Migration |
| GET |  | List Relationships |
| POST |  | Create Relationship |
| DELETE |  | Delete Relationship |

## RBAC Management  (23 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Groups |
| GET |  | Get Group |
| POST |  | Add Members To Group |
| DELETE |  | Remove Member From Group |
| POST |  | Assign Roles To Group |
| DELETE |  | Remove Role From Group |
| GET |  | Get Organization Structure |
| GET |  | Get Permission Categories |
| GET |  | List Permissions |
| GET |  | Get Grouped Permissions |
| GET |  | Get Permission |
| GET |  | List Roles |
| POST |  | Create Role |
| DELETE |  | Delete Role |
| GET |  | Get Role |
| PUT |  | Update Role |
| POST |  | Assign Permissions To Role |
| PATCH |  | Bulk Update Role Permissions |
| DELETE |  | Remove Permission From Role |
| GET |  | Get User Permissions |
| GET |  | Get User Roles |
| POST |  | Assign Roles To User |
| DELETE |  | Remove Role From User |

## org  (21 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Branches |
| POST |  | Create Branch |
| DELETE |  | Delete Branch |
| GET |  | Get Branch |
| PUT |  | Update Branch |
| GET |  | List Companies |
| POST |  | Create Company |
| DELETE |  | Delete Company |
| GET |  | Get Company |
| PUT |  | Update Company |
| GET |  | List Departments |
| POST |  | Create Department |
| DELETE |  | Delete Department |
| GET |  | Get Department |
| PUT |  | Update Department |
| GET |  | List Tenants |
| POST |  | Create Tenant |
| DELETE |  | Delete Tenant |
| GET |  | Get Tenant |
| PUT |  | Update Tenant |
| GET |  | List Users |

## Workflow Designer  (20 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Workflows |
| POST |  | Create Workflow |
| GET |  | List Instances |
| POST |  | Create Instance |
| GET |  | Get Instance |
| GET |  | Get Available Transitions |
| POST |  | Execute Transition |
| GET |  | Get Instance History |
| DELETE |  | Delete Workflow |
| GET |  | Get Workflow |
| PUT |  | Update Workflow |
| POST |  | Publish Workflow |
| POST |  | Simulate Workflow |
| GET |  | List States |
| POST |  | Create State |
| PUT |  | Update State |
| GET |  | List Transitions |
| POST |  | Create Transition |
| DELETE |  | Delete Transition |
| POST |  | Unpublish Workflow |

## reports  (17 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Report Definitions |
| POST |  | Create Report Definition |
| DELETE |  | Delete Report Definition |
| GET |  | Get Report Definition |
| PUT |  | Update Report Definition |
| POST |  | Get Join Suggestions |
| POST |  | Execute Report |
| POST |  | Execute And Export Report |
| GET |  | Get Execution History |
| POST |  | Get Lookup Data |
| POST |  | Preview Report |
| GET |  | List Report Schedules |
| POST |  | Create Report Schedule |
| DELETE |  | Delete Report Schedule |
| PUT |  | Update Report Schedule |
| GET |  | List Report Templates |
| POST |  | Create From Template |

## dashboards  (16 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Dashboards |
| POST |  | Create Dashboard |
| POST |  | Create Page |
| DELETE |  | Delete Page |
| PUT |  | Update Page |
| POST |  | Create Share |
| POST |  | Create Snapshot |
| POST |  | Create Widget |
| POST |  | Bulk Update Widgets |
| POST |  | Get Widget Data |
| DELETE |  | Delete Widget |
| PUT |  | Update Widget |
| DELETE |  | Delete Dashboard |
| GET |  | Get Dashboard |
| PUT |  | Update Dashboard |
| POST |  | Clone Dashboard |

## Automation System  (16 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Action Templates |
| GET |  | List Automation Executions |
| GET |  | Get Automation Execution |
| GET |  | List Automation Rules |
| POST |  | Create Automation Rule |
| DELETE |  | Delete Automation Rule |
| GET |  | Get Automation Rule |
| PUT |  | Update Automation Rule |
| POST |  | Execute Automation Rule |
| POST |  | Test Automation Rule |
| POST |  | Toggle Automation Rule |
| GET |  | List Webhook Configs |
| POST |  | Create Webhook Config |
| DELETE |  | Delete Webhook Config |
| GET |  | Get Webhook Config |
| PUT |  | Update Webhook Config |

## modules  (16 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Modules |
| POST |  | Create Module |
| POST |  | Validate Name |
| POST |  | Validate Prefix |
| DELETE |  | Delete Module |
| GET |  | Get Module |
| PUT |  | Update Module |
| GET |  | Get Module Components |
| GET |  | List Dependencies |
| POST |  | Add Dependency |
| GET |  | Check Dependency Compatibility |
| DELETE |  | Remove Dependency |
| GET |  | List Dependents |
| POST |  | Publish Module |
| GET |  | List Versions |
| POST |  | Create Version |

## module-registry  (14 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Available Modules |
| POST |  | Disable Module |
| POST |  | Enable Module |
| GET |  | List Enabled Modules |
| GET |  | List All Tenants Modules |
| GET |  | List Enabled Module Names |
| POST |  | Install Module |
| POST |  | Register Module |
| POST |  | Sync Modules |
| POST |  | Uninstall Module |
| GET |  | Get Module Info |
| PUT |  | Update Module Configuration |
| POST |  | Module Heartbeat |
| GET |  | Get Module Manifest |

## scheduler  (14 ops)

| Method | Path | Summary |
|---|---|---|
| POST |  | Create Scheduler Config |
| GET |  | Get Effective Config |
| DELETE |  | Delete Scheduler Config |
| GET |  | Get Scheduler Config |
| PUT |  | Update Scheduler Config |
| GET |  | Get Job Execution |
| GET |  | Get Execution Logs |
| GET |  | List Scheduler Jobs |
| POST |  | Create Scheduler Job |
| DELETE |  | Delete Scheduler Job |
| GET |  | Get Scheduler Job |
| PUT |  | Update Scheduler Job |
| POST |  | Execute Job Manually |
| GET |  | List Job Executions |

## admin  (14 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Locked Accounts |
| GET |  | List Login Attempts |
| GET |  | List Notification Configs |
| PUT |  | Update Notification Config |
| GET |  | List Notification Queue |
| GET |  | List Security Policies |
| POST |  | Create Security Policy |
| DELETE |  | Delete Security Policy |
| GET |  | Get Security Policy |
| PUT |  | Update Security Policy |
| GET |  | List Active Sessions |
| POST |  | Revoke Session |
| POST |  | Revoke All User Sessions |
| POST |  | Unlock Account |

## security  (14 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Locked Accounts |
| GET |  | List Login Attempts |
| GET |  | List Notification Configs |
| PUT |  | Update Notification Config |
| GET |  | List Notification Queue |
| GET |  | List Security Policies |
| POST |  | Create Security Policy |
| DELETE |  | Delete Security Policy |
| GET |  | Get Security Policy |
| PUT |  | Update Security Policy |
| GET |  | List Active Sessions |
| POST |  | Revoke Session |
| POST |  | Revoke All User Sessions |
| POST |  | Unlock Account |

## menu  (11 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | Get User Menu |
| POST |  | Create Menu Item |
| GET |  | Get All Menu Items |
| POST |  | Reorder Menu Items |
| POST |  | Sync Menu From Json |
| GET |  | Get Sync History |
| GET |  | Preview Sync |
| GET |  | Get Sync Status |
| DELETE |  | Delete Menu Item |
| GET |  | Get Menu Item |
| PUT |  | Update Menu Item |

## Dynamic Data  (11 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | Aggregate Records |
| GET |  | Get Entity Metadata |
| GET |  | List Records |
| POST |  | Create Record |
| DELETE |  | Bulk Delete Records |
| POST |  | Bulk Create Records |
| PUT |  | Bulk Update Records |
| DELETE |  | Delete Record |
| GET |  | Get Record |
| PUT |  | Update Record |
| GET |  | Get Related Records |

## builder  (10 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Pages |
| POST |  | Create Page |
| DELETE |  | Delete Page |
| GET |  | Get Page |
| PUT |  | Update Page |
| POST |  | Publish Page |
| POST |  | Restore Page Version |
| POST |  | Unpublish Page |
| GET |  | List Page Versions |
| GET |  | Get Page Version |

## auth  (9 ops)

| Method | Path | Summary |
|---|---|---|
| POST |  | Change Password |
| POST |  | Login |
| POST |  | Logout |
| GET |  | Get Me |
| PUT |  | Update Me |
| GET |  | Get Password Policy |
| POST |  | Refresh |
| POST |  | Reset Password Confirm |
| POST |  | Reset Password Request |

## Lookup Configuration  (8 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Cascading Rules |
| POST |  | Create Cascading Rule |
| GET |  | List Lookup Configurations |
| POST |  | Create Lookup Configuration |
| DELETE |  | Delete Lookup Configuration |
| GET |  | Get Lookup Configuration |
| PUT |  | Update Lookup Configuration |
| GET |  | Get Lookup Data |

## module-extensions  (7 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Entity Extensions |
| POST |  | Create Entity Extension |
| GET |  | Get Entity With Extensions |
| GET |  | List Menu Extensions |
| POST |  | Create Menu Extension |
| GET |  | List Screen Extensions |
| POST |  | Create Screen Extension |

## metadata  (6 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | List Entities |
| POST |  | Create Entity Metadata |
| DELETE |  | Delete Entity Metadata |
| GET |  | Get Entity Metadata |
| PUT |  | Update Entity Metadata |
| POST |  | Regenerate Entity Metadata |

## data  (6 ops)

| Method | Path | Summary |
|---|---|---|
| POST |  | Create Record |
| POST |  | Bulk Operation |
| POST |  | Search Data |
| DELETE |  | Delete Record |
| GET |  | Get Record |
| PUT |  | Update Record |

## audit  (4 ops)

| Method | Path | Summary |
|---|---|---|
| POST |  | List Audit Logs |
| GET |  | Get Audit Summary |
| GET |  | Get Audit Summary Short |
| GET |  | Get Audit Log |

## settings  (4 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | Get Tenant Settings |
| PUT |  | Update Tenant Settings |
| GET |  | Get User Settings |
| PUT |  | Update User Settings |

## untagged  (4 ops)

| Method | Path | Summary |
|---|---|---|
| GET |  | Root |
| GET |  | Health Check |
| GET |  | Healthz |
| GET |  | System Info |
