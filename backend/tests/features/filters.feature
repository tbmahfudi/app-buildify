Feature: Dynamic Entity Filtering, Sorting, and Pagination
  As a NoCode developer
  I want to filter, sort, and paginate records by field values
  So that I can retrieve only the data relevant to my use case

  Background:
    Given the 5 standard seed records are loaded

  Scenario Outline: Single-field filter operator
    When I list records with filter field "<field>" operator "<op>" value "<value>"
    Then the response total is <count>

    Examples:
      | field  | op          | value    | count |
      | status | eq          | active   | 3     |
      | status | ne          | active   | 2     |
      | price  | gt          | 5.00     | 2     |
      | price  | is_null     |          | 1     |
      | name   | contains    | Widget   | 3     |
      | name   | starts_with | Widget   | 3     |
      | status | in          | active   | 3     |
      | status | not_in      | active   | 2     |

  Scenario: AND compound filter
    When I list records with status "active" AND price greater than 5.00
    Then the response total is 2

  Scenario: OR compound filter
    When I list records with status "inactive" OR price less than 2.00
    Then the response total is 2

  Scenario: Filter with missing operator key returns 400
    When I list records with a filter that has no operator key
    Then the response status is 400

  Scenario Outline: Sort records
    When I list records sorted by "<field>" "<direction>"
    Then the first result price is "<expected_first>"

    Examples:
      | field | direction | expected_first |
      | price | asc       | 1.99           |
      | price | desc      | 99.99          |

  Scenario Outline: Paginate records
    When I list records with page <page> and page_size <size>
    Then the response contains <items> items and total is 5

    Examples:
      | page | size | items |
      | 1    | 2    | 2     |
      | 3    | 2    | 1     |

  Scenario: Search records by keyword
    When I search records for "Widget"
    Then the response total is at least 3

  Scenario: Search for a non-matching keyword returns empty
    When I search records for "zzznomatch"
    Then the response total is 0
