from flask import Flask, render_template, request, redirect
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'

@app.route("/index")
def index():
    cur = db_conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    cur.close()
    
    products = []
    for row in rows:
        product = {
            "name": row[0],
            "image": row[1],
            "price": row[2],
            "description": row[3]
        }
        products.append(product)
    
    return render_template("index.html", products=products)

@app.route('/confirm_purchase', methods=['POST'])
def confirm_purchase():
    # Retrieve form data
    product_name = request.form['product_name']
    product_price = request.form['product_price']
    address = request.form['address']
    payment_method = request.form['payment_method']

    insert_sql = "INSERT INTO SALES VALUES (%s,%s,%s,%s,%s)"
    cursor = db_conn.cursor()

    try:
        cursor.execute(insert_sql, (product_name,product_price,address,payment_method))
        db_conn.commit()

    except:
        print("An Exception Occured")

    finally:
        cursor.close()

    return render_template('purchase_confirmation.html', product_name=product_name, product_price=product_price, address=address, payment_method=payment_method)




@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')


@app.route("/about", methods=['GET'])
def about():
    return redirect('https://sunwaybucket.s3.amazonaws.com/ecommerce.html', code=302)

@app.route("/getemp", methods=['POST'])
def GetEmp():
    return render_template('GetEmp.html')

@app.route("/fetchdata", methods=['GET','POST'])
def GetEmpOutput():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        select_sql = "SELECT * FROM employee WHERE emp_id = %s"
        cursor = db_conn.cursor()

        try:
            cursor.execute(select_sql, (emp_id,))
            result = cursor.fetchone()
            if result:
                emp_data = {
                    "emp_id": result[0],
                    "first_name": result[1],
                    "last_name": result[2],
                    "pri_skill": result[3],
                    "location": result[4],
                    "image_url": "https://s3.{0}.amazonaws.com/{1}/emp-id-{2}_image_file".format(
                        region, bucket, emp_id)
                }
                return render_template('GetEmpOutput.html', emp_data=emp_data)
            else:
                return "Employee not found"
        except Exception as e:
            return str(e)
        finally:
            cursor.close()
    else:
        return render_template('GetEmp.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

