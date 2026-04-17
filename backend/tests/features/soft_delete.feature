Feature: Soft Delete Lifecycle
  As a NoCode developer
  I want deleted records to be hidden from all read paths
  So that my data is consistent and recoverable without physical row removal

  Background:
    Given a published entity with soft-delete enabled
    And a record exists with name "Soft Delete Target"

  Scenario: Deleted record disappears from list
    When I delete that record
    Then listing records returns 0 results

  Scenario: Deleted record returns 404 on GET by ID
    When I delete that record
    Then fetching that record by ID returns 404

  Scenario: Deleted record is excluded from aggregate COUNT
    When I delete that record
    Then COUNT(*) aggregate returns 0

  Scenario: Deleted record is excluded from keyword search
    When I delete that record
    Then searching for "UniqueSoftDeleteTarget" returns 0 results

  Scenario: Deleting an already-deleted record returns 404
    When I delete that record
    And I delete that record again
    Then the second delete response status is 404

  Scenario: Physical row remains after soft delete with deleted_at set
    When I delete that record
    Then the row still exists in the database with deleted_at populated
