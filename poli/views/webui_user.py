"""
    This file is part of Polichombr.

    (c) 2018 ANSSI-FR


    Description:
        Routes and forms parsing related to user management
"""
from flask import render_template, g, redirect, url_for, flash
from flask_security import login_user, logout_user
from flask_security import login_required, roles_required

from poli import app, api, security

from poli.models.user import User

from poli.views.forms import LoginForm, UserRegistrationForm
from poli.views.forms import ChgNameForm, ChgThemeForm
from poli.views.forms import ChgNickForm, ChgPassForm


@app.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Flask-Login.
    """
    if g.user.is_authenticated:
        return redirect(url_for('index'))

    login_form = LoginForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        user = api.usercontrol.get_by_name(username)
        if user is None:
            return redirect(url_for('login'))
        if api.usercontrol.check_user_pass(user, login_form.password.data):
            login_user(user, remember=True)
            security.datastore.commit()
            flash("Logged in!", "success")
            return redirect(url_for("index"))
        else:
            flash("Cannot login...", "error")
    return render_template('login.html', title='Sign In', form=login_form)


@app.route('/register/', methods=['GET', 'POST'])
def register_user():
    """
    User registration, if enabled in configuration file.
    """
    if g.user.is_authenticated or app.config['USERS_CAN_REGISTER'] is not True:
        return redirect(url_for('index'))
    registration_form = UserRegistrationForm()
    if registration_form.validate_on_submit():
        ret = api.usercontrol.create(registration_form.username.data,
                                     registration_form.password.data,
                                     registration_form.completename.data)
        if ret:
            return redirect(url_for('login'))
        else:
            app.logger.error("Error during user registration")
            flash("Error registering user")
    return render_template('register.html',
                           form=registration_form)


@app.route('/logout/')
@login_required
def logout():
    """
    Logout.
    """
    logout_user()
    return redirect(url_for('index'))


@app.route('/admin/', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
def admin_page():
    """
        Render the user admin page
    """
    users = User.query.all()
    return render_template("admin.html", users=users)


@app.route('/user/<int:user_id>/', methods=['GET', 'POST'])
@login_required
def view_user(user_id):
    """
        View a single user activity
        Useful for executive report
    """
    myuser = api.usercontrol.get_by_id(user_id)
    if myuser is None:
        flash("User not found...", "error")
        return redirect(url_for("index"))

    chnickform = ChgNickForm()
    chthemeform = ChgThemeForm()
    chnameform = ChgNameForm()
    chpassform = ChgPassForm()
    if myuser.id == g.user.id:
        if chthemeform.validate_on_submit():
            api.usercontrol.set_theme(myuser, chthemeform.newtheme.data)
        if chnameform.validate_on_submit():
            api.usercontrol.set_name(myuser, chnameform.newname.data)
        if chnickform.validate_on_submit():
            api.usercontrol.set_nick(myuser, chnickform.newnick.data)
        if chpassform.validate_on_submit():
            if api.usercontrol.check_user_pass(
                    myuser, chpassform.oldpass.data):
                api.usercontrol.set_pass(myuser, chpassform.password.data)
                flash("Changed user password", "success")
    return render_template('user.html',
                           chnickform=chnickform,
                           chthemeform=chthemeform,
                           chpassform=chpassform,
                           chnameform=chnameform,
                           user=myuser)


@app.route('/user/<int:user_id>/activate/', methods=['GET', 'POST'])
@login_required
@roles_required("admin")
def activate_user(user_id):
    """
        User activation for flask-security
    """
    ret = api.usercontrol.activate(user_id)
    if not ret:
        flash("Cannot activate user", "error")
    else:
        flash("activated user", "success")
    return redirect(url_for("admin_page"))


@app.route('/user/<int:user_id>/admin/', methods=['GET', 'POST'])
@login_required
@roles_required("admin")
def admin_user(user_id):
    """
        Add admin role for a user
    """
    ret = api.usercontrol.manage_admin_role(user_id)
    if not ret:
        flash("Cannot give admin to user", "error")
    else:
        flash("User %d is now an admin" % (user_id), "success")
    return redirect(url_for("admin_page"))


@app.route('/user/<int:user_id>/deactivate', methods=['GET', 'POST'])
@login_required
@roles_required("admin")
def deactivate_user(user_id):
    """
        Flask security user deactivation
    """
    ret = api.usercontrol.deactivate(user_id)
    if not ret:
        flash("Cannot deactivate user", "error")
    return redirect(url_for("admin_page"))
