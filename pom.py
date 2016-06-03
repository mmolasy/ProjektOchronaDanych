
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, session, flash
from uuid import uuid4
import random
import string
import hashlib
import crypt
import time 
import os
import math
from OpenSSL import SSL
context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('server.key')
context.use_certificate_file('server.crt') 

def entropia(tekst):
  n = len(tekst)
  i=0
  tab = []
  while i < n:
    l = 0
    for x in tab:
      if x == tekst[i]:
        l = 1
    if l == 0:
      tab.append(tekst[i])
    i = i + 1

  result = {}
  for x in tab:
     licznik = 0
     i=0
     while i<n:
       if x == tekst[i]:
         licznik = licznik + 1
       i = i+1
     result[x] = float(licznik)/n


  dlugosc = len(result)

  wynik=0
  for x,y in result.iteritems():
    if y == 1:
       tmp = 0
    else:
       tmp = math.log(y,2)
    wynik += y*tmp
  wynik *= -1.0
  return wynik;



app = Flask(__name__)
app.secret_key = 'a1s8dAS@#f=+D23d%^$$#*(T'
app_url = '/molasym/notatka'


salt = {}
entropie={}
proby = {}
notatkazal = {}
listaUz = {}
notatkazal['Krystian'] = []
notatkazal['Mateusz'] = []
proby['Krystian'] = 0
proby['Mateusz'] = 0
entropie['Mateusz'] = entropia("Molasy")
entropie['Krystian'] = entropia('Bogusz')

salt['Mateusz'] = ''.join(random.sample(string.ascii_letters, 2))
salt['Krystian'] = ''.join(random.sample(string.ascii_letters, 2))
listaUz['Mateusz'] = crypt.crypt('Molasy', salt['Mateusz'])
listaUz['Krystian'] = crypt.crypt('Bogusz', salt['Krystian'])



#from werkzeug.debug import DebuggedApplication
#app.debug = True
#app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

@app.route(app_url + '/logout')
def logout():
  session.pop('username', None)
  return redirect(app_url + '/login')

@app.route(app_url + '/')
def index():
  if 'username' not in session:
    return redirect(app_url + '/login')
  username = session['username']
  return render_template('login_success.html', link = notatkazal[session['username']], nick = session['username'], entr = round(entropie[session['username']], 2))

@app.route(app_url + '/notes', methods=['GET', 'POST'])
def shorten():
  if request.method == 'POST':
    note = request.form.get('link')
    if note.find("/>") != -1 or note.find(";") != -1 or note.find("</") != -1 or note.find("/ >") != -1 or note.find("%") != -1 or note.find("&") != -1 :
      return "Podejrzenie ataku XSS/INJECTION"
    #if 'username' not in session:
    #  return render_template('login_failure.html')
    if 'username' in session:
      notatkazal[session['username']].append(note)
      print session['username']
      return render_template('login_success.html', link = notatkazal[session['username']], nick = session['username'], entr = round(entropie[session['username']], 2))       
  if request.method == 'GET':
      return 'Zła metoda - GET'

@app.route(app_url + '/zmienhaslo', methods=['GET', 'POST'])
def haslo():
  if request.method == 'GET':
     if 'username' in session:
       return render_template('zmien_haslo.html')
     if 'username' not in session:
       return redirect(app_url + '/error')
  if request.method == 'POST':
     oldpassword = request.form.get('oldpassword')
     newpassword = request.form.get('newpassword')
     if len(newpassword) < 6:
       return "Haslo za krotkie - min 6 znakow"
     #repeat = request.form.get('repeat')
     if listaUz[session['username']] == crypt.crypt(oldpassword, salt[session['username']]):
        salt[session['username']] = ''.join(random.sample(string.ascii_letters, 2))
        listaUz[session['username']] = crypt.crypt(newpassword, salt[session['username']])
        entropie[session['username']] = entropia(newpassword)
        return render_template('login_success.html',link = notatkazal[session['username']], nick = session['username'], entr = round(entropie[session['username']], 2))
     else:
        return "Podane stare haslo jest nieprawdziwe"
        
 
@app.route(app_url + '/login', methods=['GET','POST'])
def login():
  if request.method == 'GET':
    if 'username' in session:
      return render_template('login_success.html',link = notatkazal[session['username']], nick = session['username'], entr = round(entropie[session['username']], 2))
    return render_template('login_form.html')
  if request.method == 'POST':
    znaleziono=0
    username = request.form.get('username')
    password = request.form.get('password')
    if len(username) == 0 or len(password) == 0:
      return "Pola formularza nie moga byc puste"
    for x,y in listaUz.iteritems():
      if x == username:
        znaleziono = 1
    print znaleziono
    if(znaleziono == 0):
      return render_template('login_failure.html')
    time.sleep(0.5)
    if listaUz[username] == crypt.crypt(password, salt[username]) and proby[username] <= 3:
      proby[username]=0
      session['uid'] = uuid4()
      session['username'] = username
      return render_template('login_success.html',link = notatkazal[session['username']], nick = session['username'], entr = round(entropie[session['username']], 2))
    if proby[username] > 3:
      return "Przekroczono limit logowan z blednym haslem. Skontaktuj sie z administratorem"
    proby[username] = proby[username] + 1
    return render_template('login_failure.html')

@app.route(app_url + '/error')
def ret_err():
  return render_template('brak_linka.html')

@app.route(app_url + '/nowyuzytkownik', methods=['GET','POST'])
def newuser():
  if request.method == 'GET':
     print 'get'
     if 'username' not in session:
       return render_template('nowyuser.html')
  if request.method == 'POST':
     print 'post'
     znaleziono = 0
     nazwauzytkownika = request.form.get('username1')
     haslo = request.form.get('password1')
     if len(haslo) < 6 or len(nazwauzytkownika) < 6:
       return "Nazwa uzytkownika oraz haslo musi zawierac przynajmniej 6 znakow"
     for x,y in listaUz.iteritems():
       if x == nazwauzytkownika:
         print 'zajety'  
         znaleziono = 1
     if(znaleziono == 1):
        return "Login zajety"
     if(znaleziono == 0):
        print 'lecimy dalej'
        salt[nazwauzytkownika] = ''.join(random.sample(string.ascii_letters, 2))
        listaUz[nazwauzytkownika] = crypt.crypt(haslo, salt[nazwauzytkownika])
	entropie[nazwauzytkownika] = entropia(haslo)
        notatkazal[nazwauzytkownika] = []
	proby[nazwauzytkownika] = 0
        return redirect(app_url + '/login')
 
if __name__ == '__main__':
  app.run(host='0.0.0.0', 
        debug = False/True, ssl_context=context)
