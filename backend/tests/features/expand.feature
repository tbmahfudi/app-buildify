Feature: Expand Related Records
  As a NoCode developer
  I want to inline related records in list and detail responses
  So that I can avoid extra round-trips in my frontend

  Background:
    Given a category entity and a product entity with a category_id FK field

  Scenario: Expand a valid FK field returns inlined data on list
    Given a category "Electronics" and a product linked to it
    When I list products with expand=category_id
    Then each product record has a "category_id_data" key
    And the inlined "category_id_data" has an "id" field

  Scenario: Expanding a FK that is NULL returns null for the inlined key
    Given a product with no category set
    When I list products with expand=category_id
    Then the product's "category_id_data" is null

  Scenario: Expanding an unknown field does not crash the endpoint
    When I list products with expand=not_a_real_field
    Then the response status is 200

  Scenario: Expand works on single record GET
    Given a category "Books" and a product linked to it
    When I GET that product by ID with expand=category_id
    Then the response data contains "category_id_data"
    And the "category_id_data" id matches the category id
