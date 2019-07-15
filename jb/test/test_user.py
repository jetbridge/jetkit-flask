def test_users(client, api_user, db_session):
    response = client.get("/api/user")

    # check endpoint response
    assert response.status_code == 200

    assert len(response.json) >= 2
    for user in response.json:
        assert user["id"]
        assert user["email"]
        assert user["name"]


def test_user_details(client, api_user, db_session, user, admin):
    response = client.get("/api/user/0")
    assert response.status_code == 404

    user_response = client.get(f"/api/user/{user.id}")
    assert user_response.status_code == 200

    admin_response = client.get(f"/api/user/{admin.id}")
    assert admin_response.status_code == 200

    assert user_response.json.get("id")
    assert user_response.json.get("email")
    assert user_response.json.get("name")

    assert user_response.json.get("id") is not admin_response.json.get("id")

    assert user_response.json.get("password") is None
    assert user_response.json.get("_password") is None
