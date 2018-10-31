import responder


api = responder.API()

@api.route('/test')
def test(req, resp):
    resp.text = 'Test String!\n'
