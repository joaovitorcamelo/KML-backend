import ast
import time
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpRequest
from .models import User
import gspread
from gspread import oauth
import os
import json
import google.oauth2.credentials
from dotenv import load_dotenv
import google_auth_oauthlib.flow

load_dotenv()

SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

CREDENTIALS = json.loadl(os.environ.get('CREDENTIALS'))


def delete_one(request, dre):
    try:

        email = request.session['email']
        user = User.objects.get(email=email)
        authorized_user = ast.literal_eval(user.user_key)

        gc, authorized_user = gspread.oauth_from_dict(CREDENTIALS, authorized_user)

        sh = gc.open('Medicina 259')
        worksheet = sh.sheet1

        column_values = worksheet.col_values(1)
        row_index = column_values.index(dre) + 1

        worksheet.delete_row(row_index)

        dre_sh = gc.open(dre)
        gc.del_spreadsheet(dre_sh.id)

        return HttpResponse("Removido com sucesso.")

    except:
        raise Http404("Houve um erro.")


def send_one(request, dre):
    try:

        email = request.session['email']
        user = User.objects.get(email=email)
        authorized_user = ast.literal_eval(user.user_key)

        gc, authorized_user = gspread.oauth_from_dict(CREDENTIALS, authorized_user)

        sh = gc.open('Medicina 259')
        worksheet = sh.sheet1
        column_values = worksheet.col_values(1)
        row = column_values.index(dre) + 1
        email = worksheet.row_values(row)[2]

        dre_sh = gc.open(dre)
        dre_sh.share(email_address=email, perm_type='user', role='reader', notify=True,
                     email_message="Notas atualizadas.")

        return HttpResponse("Adicionado com enviado!")

    except:
        raise Http404("Houve um erro.")


def create(request):
    try:

        email = request.session['email']
        user = User.objects.get(email=email)
        authorized_user = ast.literal_eval(user.user_key)

        gc, authorized_user = gspread.oauth_from_dict(CREDENTIALS, authorized_user)

        sh = gc.open("Medicina 259")
        worksheet = sh.sheet1
        list_rows = worksheet.get_all_values()
        header = list_rows[0]

        time.sleep(5)

        for i, row in enumerate(list_rows):
            dre = row[0].strip()
            if i == 0 or dre == "":
                pass
            else:
                name = row[1].strip()
                email = row[2].strip()

                row_index = i + 1
                my_range = "A" + str(row_index) + ":C" + str(row_index)
                worksheet.batch_update([{
                    'range': my_range,
                    'values': [[dre, name, email]],
                }])

                try:
                    new_sh = gc.open(dre)
                    new_worksheet = new_sh.sheet1
                    new_worksheet.clear()
                    new_worksheet.insert_rows([header, row], row=1)
                except gspread.exceptions.SpreadsheetNotFound:
                    gc.create(dre)
                    new_sh = gc.open(dre)
                    new_worksheet = new_sh.sheet1
                    new_worksheet.update_title("Notas " + dre)
                    new_worksheet.insert_rows([header, row], row=1)

        return HttpResponse("Planilhas criadas com sucesso!")
    except:
        raise Http404("Um erro aconteceu. Tente novamente!")


def send(request):

    email = request.session['email']
    user = User.objects.get(email=email)
    authorized_user = ast.literal_eval(user.user_key)

    gc, authorized_user = gspread.oauth_from_dict(CREDENTIALS, authorized_user)

    sh = gc.open('Medicina 259')
    worksheet = sh.sheet1
    list_rows = worksheet.get_all_values()

    for i, row in enumerate(list_rows):
        dre = row[0]
        email_student = row[2]

        if dre == "" or i == 0:
            pass
        else:
            new_sh = gc.open(dre)

            new_sh.share(
                email_student, perm_type='user', role='reader', notify=True, email_message="Notas atualizadas."
            )

            time.sleep(5)

    return HttpResponse("Envio realizado com sucesso!")


def delete(request):

    email = request.session['email']
    user = User.objects.get(email=email)

    authorized_user = ast.literal_eval(user.user_key)

    gc, authorized_user = gspread.oauth_from_dict(CREDENTIALS, authorized_user)

    sh = gc.open('Medicina 259')
    worksheet = sh.sheet1
    list_rows = worksheet.get_all_values()

    for i, row in enumerate(list_rows):
        dre = row[0]
        if i == 0 or dre == "":
            pass
        else:
            id_sh = gc.open(dre).id
            gc.del_spreadsheet(id_sh)

            time.sleep(5)

    return HttpResponse("Remoção realizada com sucesso!")


def oauth_redirect(request):

    email = request.GET.get('email')

    if 'email' in request.session and request.session['email'] == email:
        request.session['email'] = email
        return HttpResponse("Bem-vindo(a) de volta ao KML!")

    else:
        request.session['email'] = email

        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            CREDENTIALS,
            scopes=SCOPES
        )

        flow.redirect_uri = 'https://kml.onrender.com/callback'

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )

        request.session['state'] = state

        return HttpResponseRedirect(authorization_url)


def oauth_callback(request):
    state = request.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=CREDENTIALS,
        scopes=SCOPES,
        state=state
    )

    flow.redirect_uri = 'https://kml.onrender.com/callback'

    host = request.get_host()
    path = request.get_full_path()
    authorization_response = host + path
    flow.fetch_token(authorization_response=authorization_response)

    user_key = credentials_to_dict(flow.credentials)

    request.session['user_key'] = user_key

    try:
        email = request.session['email']
        user = None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user:
            user.user_key = user_key
            user.save()

        else:
            new_user = User(email=email, user_key=user_key)
            new_user.save()

        return HttpResponse("Login Efetuado. Bem-vindo(a) ao KML! Essa aba pode ser fechada.")

    except:
        raise Http404("Shit Happens.")


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}