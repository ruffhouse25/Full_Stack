from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import logging
import sys
from forms import VenueForm, ArtistForm, ShowForm

# Initialize Flask app, database, and migration
app = Flask(__name__)
app.config.from_object('config')  # Ensure config.py has your DB URI
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy=True, cascade="all, delete-orphan")


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy=True, cascade="all, delete-orphan")


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Custom Jinja Filter
@app.template_filter('datetime')
def format_datetime(value, format='medium'):
    if isinstance(value, str):
        try:
            date = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            date = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    else:
        date = value

    if format == 'full':
        format_str = "%A, %B %d, %Y at %I:%M%p"
    elif format == 'medium':
        format_str = "%b %d, %Y %I:%M%p"
    else:
        format_str = "%Y-%m-%d %H:%M:%S"

    return date.strftime(format_str)


# Routes

@app.route('/')
def index():
    return render_template('pages/home.html')

@app.route('/venues')
def venues():
    areas = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()
    data = []

    for city, state in areas:
        venues_in_area = Venue.query.filter_by(city=city, state=state).all()
        venue_data = []
        for venue in venues_in_area:
            upcoming_shows = Show.query.filter(Show.venue_id == venue.id, Show.start_time > datetime.now()).count()
            venue_data.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": upcoming_shows
            })
        data.append({
            "city": city,
            "state": state,
            "venues": venue_data
        })
    return render_template('pages/venues.html', areas=data)

@app.route('/venues/create', methods=['GET', 'POST'])
def create_venue():
    form = VenueForm()  # Initialize the Venue form
    if request.method == 'POST' and form.validate():
        try:
            venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data
            )
            db.session.add(venue)
            db.session.commit()
            flash(f'Venue {venue.name} was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Venue could not be listed.')
        finally:
            db.session.close()

        return redirect(url_for('index'))
    return render_template('forms/new_venue.html', form=form)

@app.route('/artists')
def artists():
    artists = Artist.query.all()
    return render_template('pages/artists.html', artists=artists)

@app.route('/artists/create', methods=['GET', 'POST'])
def create_artist():
    form = ArtistForm()  # Initialize the Artist form
    if request.method == 'POST' and form.validate():
        try:
            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website=form.website_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data
            )
            db.session.add(artist)
            db.session.commit()
            flash(f'Artist {artist.name} was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Artist could not be listed.')
        finally:
            db.session.close()

        return redirect(url_for('artists'))
    return render_template('forms/new_artist.html', form=form)

@app.route('/shows')
def shows():
    shows = Show.query.join(Venue).join(Artist).all()

    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create', methods=['GET', 'POST'])
def create_show():
    form = ShowForm()  # Initialize the Show form
    if request.method == 'POST' and form.validate():
        try:
            show = Show(
                artist_id=form.artist_id.data,
                venue_id=form.venue_id.data,
                start_time=form.start_time.data
            )
            db.session.add(show)
            db.session.commit()
            flash(f'Show for {show.artist.name} at {show.venue.name} was successfully listed!')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Show could not be listed.')
        finally:
            db.session.close()

        return redirect(url_for('shows'))
    return render_template('forms/new_show.html', form=form)

# Venue Detail Route
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    now = datetime.utcnow()

    past_shows = []
    upcoming_shows = []

    for show in venue.shows:
        show_data = {
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        if show.start_time > now:
            upcoming_shows.append(show_data)
        else:
            past_shows.append(show_data)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

    return render_template('pages/show_venue.html', venue=data)


# Artist Detail Route
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    now = datetime.utcnow()

    past_shows = []
    upcoming_shows = []

    for show in artist.shows:
        show_data = {
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        if show.start_time > now:
            upcoming_shows.append(show_data)
        else:
            past_shows.append(show_data)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

    return render_template('pages/show_artist.html', artist=data)

    
@app.route('/artists/search', methods=['GET', 'POST'])
def search_artists():
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        page = 1
    else:
        search_term = request.args.get('search_term', '')
        page = request.args.get('page', 1, type=int)

    results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).paginate(page=page, per_page=10)

    return render_template('pages/search_artists.html', results=results, search_term=search_term)




@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

    response = {
        "count": len(results),
        "data": [{"id": v.id, "name": v.name} for v in results]
    }

    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=search_term
    )


@app.route('/artists/<int:artist_id>/edit', methods=['GET', 'POST'])
def edit_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    form = ArtistForm(obj=artist)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            form.populate_obj(artist)
            db.session.commit()
            flash('Artist updated successfully!')
            return redirect(url_for('show_artist', artist_id=artist.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Artist could not be updated.')
            print(e)
    return render_template('forms/edit_artist.html', form=form, artist=artist)



@app.route('/venues/<int:venue_id>/edit', methods=['GET', 'POST'])
def edit_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm(obj=venue)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            form.populate_obj(venue)
            db.session.commit()
            flash('Venue updated successfully!')
            return redirect(url_for('show_venue', venue_id=venue.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Venue could not be updated.')
            print(e)
    return render_template('forms/edit_venue.html', form=form, venue=venue)




# Error Handlers

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Logging
if not app.debug:
    file_handler = logging.FileHandler('error.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

# Launch
if __name__ == '__main__':
    app.run(debug=True)
