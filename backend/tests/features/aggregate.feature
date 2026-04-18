Feature: Dynamic Entity Aggregation
  As a NoCode developer
  I want to run aggregate queries on my entity data
  So that I can generate reports and dashboards without writing SQL

  Background:
    Given the 5 standard seed records are loaded

  Scenario: COUNT all records with no group-by
    When I aggregate COUNT(*) with no group-by
    Then the result has 1 group
    And the group value "total_records" is 5

  Scenario: COUNT records grouped by status
    When I aggregate COUNT(id) grouped by status
    Then the result has 3 groups

  Scenario: SUM price grouped by status
    When I aggregate SUM(price) grouped by status
    Then the result has 3 groups

  Scenario: SUM price for active records only
    When I aggregate SUM(price) grouped by status filtered to status "active"
    Then the result has 1 group
    And the group value "total_price" is approximately 17.97

  Scenario: MIN and MAX quantity with no group-by
    When I aggregate MIN(quantity) and MAX(quantity) with no group-by
    Then the group value "min_qty" is 0
    And the group value "max_qty" is 20

  Scenario: COUNT DISTINCT status values
    When I aggregate COUNT DISTINCT on status
    Then the result has 1 group
    And the group value "distinct_statuses" is 3

  Scenario: Multiple metrics in one query
    When I aggregate SUM(price) and COUNT(id) grouped by status
    Then the result has 3 groups

  Scenario: Group by date truncated to month
    When I aggregate COUNT(id) grouped by created_at truncated to month
    Then the result has 1 group

  Scenario: Unsupported metric function returns 400
    When I aggregate with an unsupported function "median" on field "price"
    Then the response status is 400

  Scenario: Empty metrics list returns 400
    When I aggregate with an empty metrics list
    Then the response status is 400

  Scenario: Soft-deleted record is excluded from COUNT
    Given 1 record is deleted
    When I aggregate COUNT(*) with no group-by
    Then the group value "n" is 4
