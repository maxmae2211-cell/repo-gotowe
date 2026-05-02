*** Settings ***
Library    Collections
Library    RequestsLibrary

*** Variables ***
${BASE_URL}    https://jsonplaceholder.typicode.com

*** Test Cases ***
GET Posts Should Return 200
    Create Session    api    ${BASE_URL}
    ${response}=    GET On Session    api    /posts
    Should Be Equal As Integers    ${response.status_code}    200
    Log    Posts count: ${response.json().__len__()}

GET Single Post Should Return Correct Data
    Create Session    api    ${BASE_URL}
    ${response}=    GET On Session    api    /posts/1
    Should Be Equal As Integers    ${response.status_code}    200
    Dictionary Should Contain Key    ${response.json()}    title
    Dictionary Should Contain Key    ${response.json()}    body

GET Users Should Return List
    Create Session    api    ${BASE_URL}
    ${response}=    GET On Session    api    /users
    Should Be Equal As Integers    ${response.status_code}    200
    Length Should Be    ${response.json()}    10
