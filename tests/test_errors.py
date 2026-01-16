def test_404(client):
    response = client.get("/no-existe")
    assert response.status_code == 404
    
def test_method_not_allowed(client):
    res = client.post("/")
    assert res.status_code == 405
