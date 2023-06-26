import os
from time import sleep

from garden_water.database import TimersDatabase
from microWebSrv import MicroWebSrv

DATABASE_LOCATION = os.getenv("GARDEN_WATER_DATABASE_LOCATION", "/garden-water.sqlite")
TIMERS_CONTAINER_SINGLETON = TimersDatabase(DATABASE_LOCATION)


@MicroWebSrv.route("/timers", "GET")
def get_timers(httpClient, httpResponse):
    content = ""
    httpResponse.WriteResponseOk(headers=None, contentType="application/json", contentCharset="UTF-8", content=content)


@MicroWebSrv.route("/test", "POST")
def _httpHandlerTestPost(httpClient, httpResponse):
    formData = httpClient.ReadRequestPostedFormData()
    firstname = formData["firstname"]
    lastname = formData["lastname"]
    content = """\
    <!DOCTYPE html>
    <html lang=en>
        <head>
            <meta charset="UTF-8" />
            <title>TEST POST</title>
        </head>
        <body>
            <h1>TEST POST</h1>
            Firstname = %s<br />
            Lastname = %s<br />
        </body>
    </html>
    """ % (
        MicroWebSrv.HTMLEscape(firstname),
        MicroWebSrv.HTMLEscape(lastname),
    )
    httpResponse.WriteResponseOk(headers=None, contentType="text/html", contentCharset="UTF-8", content=content)


# @MicroWebSrv.route("/edit/<index>")  # <IP>/edit/123           ->   args['index']=123
# @MicroWebSrv.route("/edit/<index>/abc/<foo>")  # <IP>/edit/123/abc/bar   ->   args['index']=123  args['foo']='bar'
# @MicroWebSrv.route("/edit")  # <IP>/edit               ->   args={}
# def _httpHandlerEditWithArgs(httpClient, httpResponse, args={}):


srv = MicroWebSrv(webPath="www/")
srv.MaxWebSocketRecvLen = 256
srv.WebSocketThreaded = True
srv.Start(threaded=True)

print("Hello world")

while True:
    sleep(999999)

# ----------------------------------------------------------------------------
