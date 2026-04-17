Feature: Dynamic Query Builder (unit)
  As a backend developer
  I want DynamicQueryBuilder to translate filter and aggregate dicts into SQL
  So that query logic is correct across any entity model

  Scenario Outline: Build a valid single-condition filter clause
    When I build a filter for field "<field>" with operator "<op>"
    Then the compiled SQL contains "<field>"

    Examples:
      | field  | op          |
      | status | eq          |
      | status | ne          |
      | price  | gt          |
      | price  | gte         |
      | price  | lt          |
      | price  | lte         |
      | name   | contains    |
      | name   | starts_with |
      | name   | ends_with   |
      | status | in          |
      | status | not_in      |
      | price  | is_null     |
      | price  | is_not_null |
      | name   | like        |
      | name   | ilike       |

  Scenario: AND compound filter includes both conditions
    When I build an AND compound filter for status "active" and price > 5
    Then the compiled SQL contains "status"

  Scenario: OR compound filter includes both conditions
    When I build an OR compound filter for status "inactive" and price < 2
    Then the compiled SQL contains "status"

  Scenario: Empty filter dict returns None
    When I build a filter from an empty dict
    Then the filter clause is None

  Scenario: Empty conditions list returns None
    When I build an AND filter with an empty conditions list
    Then the filter clause is None

  Scenario: Compound filter missing the operator key raises ValueError
    When I build a filter with conditions but no operator key
    Then a ValueError is raised

  Scenario: Unknown operator raises ValueError
    When I build a filter with unsupported operator "regex"
    Then a ValueError is raised

  Scenario: Filter on a non-existent field raises ValueError
    When I build a filter for field "nonexistent_field" with operator "eq"
    Then a ValueError is raised

  Scenario Outline: Build a valid aggregate select
    When I build an aggregate with function "<function>" on field "<field>" aliased "<alias>"
    Then the output keys contain "<alias>"
    And the select column count is <cols>

    Examples:
      | function       | field    | alias             | cols |
      | count          | *        | total             | 1    |
      | sum            | price    | total_price       | 1    |
      | avg            | price    | avg_price         | 1    |
      | min            | quantity | min_qty           | 1    |
      | max            | quantity | max_qty           | 1    |
      | count_distinct | status   | distinct_statuses | 1    |

  Scenario: Aggregate with group-by produces extra select column
    When I build an aggregate with SUM(price) grouped by status
    Then the select column count is 2
    And the output keys contain "status"

  Scenario: Auto-alias is function_field when alias is omitted
    When I build an aggregate with function "sum" on field "price" with no alias
    Then the output keys contain "sum_price"

  Scenario: Unknown aggregate function raises ValueError
    When I build an aggregate with function "median" on field "price"
    Then a ValueError is raised

  Scenario: Aggregate on non-existent field raises ValueError
    When I build an aggregate with function "sum" on field "ghost_field"
    Then a ValueError is raised

  Scenario: Group-by on non-existent field raises ValueError
    When I build an aggregate with COUNT(*) grouped by "nonexistent"
    Then a ValueError is raised
