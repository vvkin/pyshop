import os

from flask import redirect, render_template, request, url_for, current_app, jsonify, send_from_directory
from flask_paginate import Pagination
from app.admin import admin
from app.admin.forms import ProductForm, ProductFilterForm
from app.decorators import admin_required
from app.models import User, Supplier, Category, Product


@admin.route('/', methods=['GET', 'POST'])
@admin_required
def panel():
    return render_template('admin/panel.html')

@admin.route('/users', methods=['GET'])
@admin_required
def users():
    q = request.args.get('q')
    search = q is not None
    page = request.args.get('page', type=int, default=1)
    total, users = User.get_paginated_users(page=page)
    pagination = Pagination(page=page, total=total, search=search, css_framework='foundation', 
        per_page=User.per_page)
    return render_template('admin/users.html', users=users, pagination=pagination)

@admin.route('/products', methods=['GET', 'POST'])
@admin_required
def product_list():
    form = ProductFilterForm()

    if form.validate_on_submit():
        if form.reset.data: return redirect(url_for('admin.product_list'))

        elif form.search.data or form.query.data:

            data = {'value': form.filter_mode.data, 'query': form.query.data}
            pagination, products = Product.get_paginated_by(data, request.args)
            return render_template('admin/product_list.html', form=form,
                products=products, pagination=pagination
            )

    elif request.args.get('page'):
        data = {'value': Product.last_option, 'query': Product.last_query}
        pagination, products = Product.get_paginated_by(data, request.args)
        return render_template('admin/product_list.html', form=form,
                products=products, pagination=pagination
        )

    pagination, products = Product.get_paginated_by({'value': 0}, request.args)
    return render_template('admin/product_list.html', form=form, 
        products=products, pagination=pagination
    )

@admin.route('/products/add', methods=['GET', 'POST'])
@admin_required
def product_add():
    form = ProductForm()
    form.category_id.choices = Category.get_all_choices()
    form.supplier_id.choices = Supplier.get_all_choices()

    if form.validate_on_submit():
        Product.save_product(
            form.supplier_id.data,
            form.category_id.data,
            form.product_name.data,
            form.sku.data,
            form.unit_price.data,
            form.discount.data,
            form.units_in_stock.data,
            form.description.data
        )    
        Product.save_images(request.files.getlist('images'), form.sku.data)
        if form.save.data: return redirect(url_for('admin.panel'))
        else: return redirect(url_for('admin.product_add'))
    
    return render_template('admin/product_add.html', form=form)

@admin.route('/products/update/<int:pk>', methods=['GET', 'POST'])
@admin_required
def product_update(pk):
    form = ProductForm()
    form.category_id.choices = Category.get_all_choices()
    form.supplier_id.choices = Supplier.get_all_choices()

    if form.validate_on_submit():
        Product.update_product(
            pk,
            form.supplier_id.data,
            form.category_id.data,
            form.product_name.data,
            form.sku.data,
            form.unit_price.data,
            form.discount.data,
            form.units_in_stock.data,
            form.description.data
        )
        Product.save_images(request.files.getlist('images'), form.sku.data)
        if form.save.data: return redirect(url_for('admin.panel'))
        else: return redirect(url_for('admin.product_update', pk=pk))
    
    return render_template('admin/product_update.html', form=form, pk=pk)

@admin.route('/products/<int:pk>', methods=['DELETE'])
@admin_required
def product_delete(pk):
    Product.delete(pk)
    return {'success': True}

@admin.route('/products/<int:pk>', methods=['GET'])
@admin_required
def product_get(pk):
    response = Product.get_json(pk)
    return response

@admin.route('/products/<int:pk>/images', methods=['GET'])
def product_images(pk):
    img_dir = '/'.join(['products', str(pk)])
    img_path = os.path.join(current_app.config['UPLOAD_PATH'], img_dir)
    img_names = os.listdir(img_path) if os.path.exists(img_path) else []
    images = [url_for('static', filename=os.path.join(img_dir, img)) for img in img_names]
    return jsonify(images=images)
