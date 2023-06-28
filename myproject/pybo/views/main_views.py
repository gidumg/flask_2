from flask import Blueprint, render_template, request
from markupsafe import Markup
import pandas as pd
import os
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import pandas as pd
from IPython.display import display, HTML
import pymysql
from sqlalchemy import text
from flask import Flask
from flask import Blueprint, url_for
from werkzeug.utils import redirect
from flask import current_app as app


bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        result = ""
        if uploaded_file.filename != '':
            # Ensure the upload directory exists
            upload_dir = os.path.join(app.root_path, 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
        
        # Save the uploaded file
        file_path = os.path.join(upload_dir, uploaded_file.filename)
        uploaded_file.save(file_path)  # save file
        result = process_file(file_path)  # process file
        os.remove(file_path)  # delete file after processing

    else:
        result = "아직 파일이 업로드 되지 않았습니다."

    return render_template('index.html', result=result)


def process_file(filename):

    file_list = pd.read_excel(filename, header=0, sheet_name=0)
    password = quote_plus('!!@Ll752515')

    # SQL에서 프로킷 / 컴스마트 정보 가져오기

    engine = create_engine(f'mysql+pymysql://fred:{password}@fred1234.synology.me/fred')
    query = """select `주문코드`, `바코드`, `상품명`, `모델명`, `총재고(H)`, `허브매장(U)`, `본사재고(B)`, `판매가`, `도매가`,`파트너가`,` 상품이미지1`  from comsmart_web """
    comsmart_df = pd.read_sql(query, con=engine)

    find_items = file_list.merge(comsmart_df, on="주문코드", how="left")

    find_items['총재고(H)']  = find_items["총재고(H)"].str.replace("품절","0")
    find_items['총재고(H)']  = find_items["총재고(H)"].str.replace(",","")
    find_items['총재고(H)']  = find_items["총재고(H)"].astype("Int64")
    find_items['허브매장(U)']  = find_items["허브매장(U)"].astype("Int64")
    find_items['본사재고(B)']  = find_items["본사재고(B)"].astype("Int64")
    find_items['판매가']  = find_items["판매가"].astype("Int64")
    find_items['도매가']  = find_items["도매가"].astype("Int64")
    find_items['파트너가']  = find_items["파트너가"].astype("Int64")


    find_items2 = find_items[['주문코드', '바코드', '상품명', '총재고(H)', '허브매장(U)','본사재고(B)','판매가','도매가','파트너가', ' 상품이미지1' ]]


    # 각 이미지 링크를 HTML 이미지 태그로 변환
    find_items2[' 상품이미지1'] = find_items2[' 상품이미지1'].apply(lambda x: f'<img src="{x}" width="100">')
    # 데이터프레임을 HTML로 변환
    html = find_items2.to_html(escape=False)

    css_style = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
    </style>
    """

    # CSS 스타일을 HTML에 적용합니다.
    html_with_style = css_style + html

    return Markup(html_with_style)


####################################################################################################################


@bp.route('/search', methods=['POST'])
def search_model():
    model_name = request.form.get('model_name')
    password = quote_plus('!!@Ll752515')
    # SQL에서 모델 정보 가져오기

    engine = create_engine(f'mysql+pymysql://fred:{password}@fred1234.synology.me/fred')
    # 완벽하게 일치하는 경우 찾기
    query = text("SELECT * FROM comsmart_web WHERE `주문코드` = :model_name")
    items = pd.read_sql_query(query, con=engine, params={'model_name': model_name})

    if items.empty:
        query = text("SELECT * FROM comsmart_web WHERE `주문코드` LIKE :model_name")
        items = pd.read_sql_query(query, con=engine, params={'model_name': model_name+'%'})


    find_items2 = items[['주문코드', '바코드','판매가','도매가','파트너가', ' 상품이미지1' ]]


    query = text("SELECT * FROM comsmart_database WHERE `주문코드` LIKE :model_name")
    comsmart_db = pd.read_sql_query(query, con=engine, params={'model_name': model_name+'%'})

    comsmart_db = comsmart_db[['주문코드', '제품명', '합계', '본사', '용산허브', '일산창고']]

    merged_df = find_items2.merge(comsmart_db, on='주문코드', how="left")
    merged_df = merged_df[['주문코드', '바코드', '제품명', '합계', '본사', '용산허브', '일산창고', ' 상품이미지1']]


    # 각 이미지 링크를 HTML 이미지 태그로 변환
    merged_df[' 상품이미지1'] = merged_df[' 상품이미지1'].apply(lambda x: f'<img src="{x}" width="100">')
    # 데이터프레임을 HTML로 변환

    # 데이터프레임을 HTML로 변환
    html = merged_df.to_html(escape=False)

    css_style = """
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
    </style>
    """

    # CSS 스타일을 HTML에 적용합니다.
    result = Markup(css_style + html)

    return render_template('index.html', result=result)