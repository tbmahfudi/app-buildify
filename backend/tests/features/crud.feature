Feature: Dynamic Entity CRUD
  As a NoCode developer
  I want to create, read, update, and delete records in a custom entity
  So that I can manage business data without writing code

  Background:
    Given a published entity with standard fields

  Scenario: Create a record with all fields
    When I create a record with name "Widget A" price "9.99" status "active"
    Then the response status is 201
    And the response body contains an "id" field

  Scenario: Create a record with only the required name field
    When I create a record with name "Widget B"
    Then the response status is 201

  Scenario: Creating a record without the required name field returns 422
    When I create a record with price "5.00" and no name
    Then the response status is 422

  Scenario: Extra unknown fields are accepted and stripped
    When I create a record with name "Widget X" and an extra field "nonexistent"
    Then the response status is 201

  Scenario: Read an existing record by ID
    Given a record exists with name "Read Me"
    When I fetch that record by its ID
    Then the response status is 200
    And the record data name is "Read Me"

  Scenario: Reading a non-existent record returns 404
    When I fetch a record with a random unknown ID
    Then the response status is 404

  Scenario: Update a record's name
    Given a record exists with name "Old Name"
    When I update that record with name "New Name"
    Then the response status is 200
    And the record data name is "New Name"

  Scenario: Delete a record returns 204
    Given a record exists with name "To Delete"
    When I delete that record
    Then the response status is 204
