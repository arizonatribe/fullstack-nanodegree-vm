#  -*- coding: utf-8 -*-
import cgi
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

# Connect to the restaurants database
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

# reusable HTML and CSS markup common to all the pages being rendered
def get_page_template(content):
    return "<html><head><title>Restaurants</title><meta http-equiv='Content-Type' content='text/html; charset=utf-8'></head><body>" \
        "<style>"\
        " body { padding: 0; margin: 0; background-color: #f2f2f2; font-family: Arial; font-size: 12px; } " \
        " .content { display: block; padding: 2em; text-align: center; }" \
        " h1, h2, h3, h4 { color: #666; font-family: 'Arial Black', Helvetica, sans-serif; } " \
        " header { margin: 0 auto; text-align: center; background-color: #999999; height: 70px; } header h1 { color: #e2e2e2; display: block; font-size: 36px; padding-top: 20px; }" \
        " .restaurant { font-size: 14px; transition: all ease 0.2s; text-align: center; opacity: 0.9; max-width: 400px; display: block; font-family: Arial, Helvetica; list-style: none; padding: 1em; border-radius: 4px; border: 1px solid #666; margin-top: 0.3em; color: #333; background-color: #b3b3b3; }" \
        " .restaurant:hover { background-color: #e2e2e2; } ul { margin: 0 auto; display: block; text-align: center; padding: 0; max-width: 400px; } " \
        " .restaurant span { display: block; font-size: 24px; margin: 0.5em auto; } " \
        " input[type=text] { padding: 0.3em; border-radius: 4px; color: #999; background-color: #ffffff; border: 1px solid #666; outline: none; }" \
        " .restaurant a, .create-new, .back-button, input[type=submit] { padding: 0.3em; transition: all ease 0.1s; margin: 0.2em; border-radius: 4px; display: inline-block; color: #f2f2f2; background-color: #999; text-decoration: none; border: none; outline: none; cursor: pointer; } " \
        " .restaurant a:hover, .create-new:hover, .back-button:hover, input[type=submit]:hover { background-color: #b30000; }" \
        " .create-new { margin-bottom: 2em; font-size: 18px; } " \
        "</style>" \
        "<header><h1> Restaurants </h1></header><div class='content'>" + content + "</div></body></html>"

class webserverHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            self.send_response(301)
            self.end_headers()

            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)

            output = ""

            if self.path.endswith("/hello"):
                hellomessage = fields.get('message')
                output += "<h2> Hello from the outside </h2>"
                output += "<h1> %s </h1>" % hellomessage[0]
                output += "<form method='POST' enctype='multipart/form-data' action='/hello'>" \
                          "<h3>Hello, how are you?</h3>" \
                          "<input name='message' type='text'><input type='submit' value='Submit'>" \
                          "</form>"

            elif self.path.endswith("/hola"):
                holamessage = fields.get('message')
                output += "<h2> Hola del exterior </h2>"
                output += "<h1> %s </h1>" % holamessage[0]
                output += "<form method='POST' enctype='multipart/form-data' action='/hola'>" \
                          "<h3>Hola,  &iquest;como estás?</h3>" \
                          "<input name='message' type='text'><input type='submit' value='Enviar'>" \
                          "</form>"

            elif self.path.endswith("/edit"):
                restaurantname = fields.get('name')
                restaurantid = fields.get('id')
                editRestaurant = session.query(Restaurant).filter_by(id = restaurantid[0]).one()
                editRestaurant.name = restaurantname[0]

                output += "<h2>Restaurant Renamed to %s </h2>" % editRestaurant.name
                output += "<a class='back-button' href='/restaurants'>Back to Restaurant List</a>"

                session.add(editRestaurant)
                session.commit()

            elif self.path.endswith("/delete"):
                restaurantid = fields.get('id')
                deleteRestaurant = session.query(Restaurant).filter_by(id = restaurantid[0]).one()

                output += "<h2> %s Removed </h2>" % deleteRestaurant.name
                output += "<a class='back-button' href='/restaurants'>Back to Restaurant List</a>"

                session.delete(deleteRestaurant)
                session.commit()

            elif self.path.endswith("/new"):
                restaurantname = fields.get('name')
                newRestaurant = Restaurant(name = restaurantname[0])

                output += "<h2>New Restaurant %s Added </h2>" % newRestaurant.name
                output += "<a class='back-button' href='/restaurants'>Back to Restaurant List</a>"

                session.add(newRestaurant)
                session.commit()

            page = get_page_template(output)
            self.wfile.write(page)
            print page

        except:
            pass

    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            output = ""

            if self.path.endswith("/hello"):
                output += "<h1>Hello!</h1><h3>It's me</h3>" \
                          "<p>I was wondering if after all these years you'd like to meet, to go over everything</p>"
                output += "<form method='POST' enctype='multipart/form-data' action='/hello'>" \
                          "<h3>Hello, can you hear me?</h3>" \
                          "<input name='message' type='text'><input type='submit' value='Submit'>" \
                          "</form>"

            elif self.path.endswith("/hola"):
                output += "<h1>&#161Hola!</h1><h3>Soy yo</h3><p>Me preguntaba si, después de tantos años Querrías verme Para hablar sobre todo</p>"
                output += "<form method='POST' enctype='multipart/form-data' action='/hola'>" \
                          "<h3>Hola, &iquest;puedes oírme?</h3>" \
                          "<input name='message' type='text'><input type='submit' value='Enviar'>" \
                          "</form>"
                output += "<a class='back-button' href='/hello'>Back to Hello</a>"

            elif self.path.endswith("/restaurants"):
                restaurants = session.query(Restaurant).all()
                output += "<a class='create-new' href='/new'>Create a New Restaurant</a>"
                output += "<ul>"
                for restaurant in restaurants:
                    print restaurant.name
                    output += "<li class='restaurant'><span>%s</span>" % restaurant.name
                    output += "<a href='/restaurants/%s/edit'>Edit</a>" % restaurant.id
                    output += "<a href='/restaurants/%s/delete'>Delete</a>" % restaurant.id
                    output += "</li>"
                output += "</ul>"

            elif self.path.endswith("/edit"):
                editId = self.path.split("/")[2]
                editRestaurant = session.query(Restaurant).filter_by(id = editId).one()

                output += "<h2> Rename %s Restaurant </h2>" % editRestaurant.name
                output += "<form method='POST' enctype='multipart/form-data' action='/edit'>" \
                          "<input type='hidden' name='id' value='%s'><input name='name' type='text' value='%s'><input type='submit' value='Submit'>" \
                          "</form>" % (editId, editRestaurant.name)
                output += "<a class='back-button' href='/restaurants'>Cancel</a>"

            elif self.path.endswith("/new"):
                output += "<h2> Create a New Restaurant </h2>"
                output += "<form method='POST' enctype='multipart/form-data' action='/new'>" \
                          "<input name='name' type='text'><input type='submit' value='Submit'>" \
                          "</form>"
                output += "<a class='back-button' href='/restaurants'>Cancel</a>"

            elif self.path.endswith("/delete"):
                deleteId = self.path.split("/")[2]
                deleteRestaurant = session.query(Restaurant).filter_by(id = deleteId).one()

                output += "<h2> Are you sure you want to Delete %s? </h2>" % deleteRestaurant.name
                output += "<form method='POST' enctype='multipart/form-data' action='/delete'>" \
                          "<input type='hidden' name='id' value='%s'><input type='submit' value='Delete'>" \
                          "<a class='back-button' href='/restaurants'>Cancel</a>" \
                          "</form>" % deleteId

            page = get_page_template(output)
            self.wfile.write(page)
            print page
            return

        except IOError:
            self.send_error(404, "File Not Found %s" % self.path)
def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webserverHandler)
        print "Web server running on port %s" % port
        server.serve_forever()

    except KeyboardInterrupt:
        print "^C entered, stopping web server..."
        server.socket.close()

if __name__ == '__main__':
    main()