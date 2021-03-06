import urllib
import re
from flask import session, redirect, url_for, escape, request, render_template, make_response

from requestbin import app, db

def update_recent_bins(name):
    if 'recent' not in session:
        session['recent'] = []
    if name in session['recent']:
        session['recent'].remove(name)
    session['recent'].insert(0, name)
    if len(session['recent']) > 10:
        session['recent'] = session['recent'][:10]
    session.modified = True


def expand_recent_bins():
    if 'recent' not in session:
        session['recent'] = []
    recent = []
    for name in session['recent']:
        try:
            recent.append(db.lookup_bin(name))
        except KeyError:
            session['recent'].remove(name)
            session.modified = True
    return recent

@app.endpoint('views.home')
def home():
    return render_template('home.html', recent=expand_recent_bins())


@app.endpoint('views.bin')
def bin(name):
    regexMerchant = re.compile(r'^m([a-zA-Z0-9]{19})')

    try:
        bin = db.lookup_bin(name)
    except KeyError:
        if regexMerchant.match(name):
            bin = db.create_bin_with_name("",name)
        else:
            return "Not found\n", 404
    if request.query_string == 'inspect':
        if bin.private and session.get(bin.name) != bin.secret_key:
            return "Private bin\n", 403
        update_recent_bins(name)
        return render_template('bin.html',
            bin=bin,
            base_url=request.scheme+'://'+request.host)
    else:
        db.create_request(bin, request)
        resp = make_response("ok\n")
        resp.headers['Sponsored-By'] = "https://www.runscope.com"
        return resp

@app.endpoint('views.bin.redirect')
def bin_redirect(name, redirect_to):
    regexMerchant = re.compile(r'^m([a-zA-Z0-9]{19})')

    try:
        bin = db.lookup_bin(name)
    except KeyError:
        if regexMerchant.match(name):
            bin = db.create_bin_with_name("",name)
        else:
            return "Not found\n", 404
    if request.query_string == 'inspect':
        if bin.private and session.get(bin.name) != bin.secret_key:
            return "Private bin\n", 403
        update_recent_bins(name)
        return render_template('bin.html',
            bin=bin,
            base_url=request.scheme+'://'+request.host)
    else:
        db.create_request(bin, request)
        resp = make_response("ok\n")
        resp.headers['Sponsored-By'] = "https://www.runscope.com"
        return redirect(redirect_to, code=302, Response=None)

@app.endpoint('views.docs')
def docs(name):
    doc = db.lookup_doc(name)
    if doc:
        return render_template('doc.html',
                content=doc['content'],
                title=doc['title'],
                recent=expand_recent_bins())
    else:
        return "Not found", 404
