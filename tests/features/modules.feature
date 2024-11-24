Feature: Modules
    Background:
        Given a mocked channel
        And a mocked repository

    Scenario: Get modules after initialization
        When the client requests /modules
        Then the client receives []

    Scenario: Get modules after adding a module
        When the channel receives a message on topic 'modules' with content
            {
                "name": "test",
                "version": "1.0.0"
            }
        And the client requests /modules
        Then the client receives [{"name": "test", "version": "1.0.0"}]