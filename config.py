

app_route = {
    'private': 'socketio.run(app)',
    'public': 'socketio.run(app, host="0.0.0.0", port=80)'
}

chat_route = {
    'private': '''var sio = io('http://127.0.0.1:5000/'+location.pathname.split('/')[2]);''',
    'public': '''var sio = io('http://' + location.hostname + '/' + location.pathname.split('/')[2])'''
}
