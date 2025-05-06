from flask import Flask, jsonify, render_template, redirect
from sqlalchemy import func, desc, distinct, inspect, MetaData, Table, Column, Integer, String, Float, create_engine
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)
app.config['DEBUG'] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True

#################################################
# Database Setup
#################################################

# Using SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///olympics.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy with app
db = SQLAlchemy(app)

# Create the database and tables if they don't exist
def create_db_from_csv():
    """Create SQLite database from CSV files if it doesn't exist"""
    # Check if database already exists
    if os.path.exists('olympics.db'):
        logger.info("Database already exists, skipping creation")
        return
    
    try:
        # Create connection to SQLite database
        conn = sqlite3.connect('olympics.db')
        
        # Load CSV files into pandas DataFrames
        logger.info("Loading CSV files...")
        host_country_df = pd.read_csv("data/host_country.csv")
        summer_olympics_host_df = pd.read_csv("data/Summer_Olympics_Host.csv")
        summer_athlete_medals_df = pd.read_csv("data/summer_athlete_medals_count.csv")
        
        # Write DataFrames to SQLite tables
        logger.info("Creating database tables...")
        host_country_df.to_sql('host_country', conn, index=False, if_exists='replace')
        summer_olympics_host_df.to_sql('summer_olympics_host', conn, index=False, if_exists='replace')
        summer_athlete_medals_df.to_sql('athletes', conn, index=False, if_exists='replace')
        
        conn.close()
        logger.info("Database created successfully from CSV files")
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise

# Create the database from CSV files
with app.app_context():
    create_db_from_csv()

# Define the Athletes model
class Athletes(db.Model):
    __tablename__ = 'athletes'
    
    id = Column(Integer, primary_key=True)
    Year = Column(Integer)
    Country = Column(String)
    Host = Column(Integer)
    Athletes = Column(Integer)
    Sports = Column(Integer)
    Events = Column(Integer)
    Gold = Column(Integer)
    Silver = Column(Integer)
    Bronze = Column(Integer)
    Medals = Column(Integer)
    
    def __repr__(self):
        return f'<Athlete {self.Country}>'

# Define the Host Country model
class HostCountry(db.Model):
    __tablename__ = 'host_country'
    
    id = Column(Integer, primary_key=True)
    Year = Column(Integer)
    Country = Column(String)
    City = Column(String)
    
    def __repr__(self):
        return f'<Host {self.Country}>'

# Define the Summer Olympics Host model
class SummerOlympicsHost(db.Model):
    __tablename__ = 'summer_olympics_host'
    
    id = Column(Integer, primary_key=True)
    Year = Column(Integer)
    Host = Column(String)
    
    def __repr__(self):
        return f'<SummerHost {self.Host}>'

#################################################
# Flask Routes
#################################################

@app.route("/index.html")
def home():
    """Return the homepage."""
    try:
        return render_template("index1.html")
    except Exception as e:
        logger.error(f"Error loading homepage: {str(e)}")
        return jsonify({"error": str(e)}), 500

# @app.route("/analysis")
# def analysis():
#     """Return the analysis page."""
#     try:
#         return render_template("analysis1.html")
#     except Exception as e:
#         logger.error(f"Error loading analysis page: {str(e)}")
#         return jsonify({"error": str(e)}), 500

@app.route("/")
def analysis():
    try:
        return render_template("analysis1.html")
    except Exception as e:
        print(f"Error: {str(e)}")  # This will print to your console
        return f"An error occurred: {str(e)}", 500


@app.route("/olympic_facts.html")
def olympic_facts():
    """Return the Olympic facts page."""
    try:
        return render_template("olympic_facts.html")
    except Exception as e:
        logger.error(f"Error loading Olympic facts page: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/machine_learning")
def machine_learning():
    """Return the machine learning page."""
    try:
        return render_template("machine_learning.html")
    except Exception as e:
        logger.error(f"Error loading machine learning page: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# API Routes
@app.route("/api/all-medal-winners")
@app.route("/api/all-medal-winners/<country_name>")
def entire_data_dump(country_name=None):
    """
    Return the list for all players who won a medal in Olympics based on input parameter
    
    Parameters:
    country_name (str, optional): Filter results by country name
    
    Returns:
    JSON: List of dictionaries containing medal data
    """
    try:
        query = db.session.query(
            Athletes.Year,
            Athletes.Country,
            Athletes.Athletes,
            Athletes.Sports,
            Athletes.Events,
            Athletes.Gold,
            Athletes.Silver,
            Athletes.Bronze,
            Athletes.Medals
        ).filter(Athletes.Medals > 0)
        
        if country_name is not None:
            query = query.filter(Athletes.Country.ilike(f'%{country_name}%'))
    
        query = query.order_by(Athletes.Year, Athletes.Country)
        
        all_athletes = []

        for year, country, athletes, sports, events, gold, silver, bronze, medals in query.all():
            athlete_dict = {
                "year": year,
                "country": country,
                "athletes": athletes,
                "sports": sports,
                "events": events,
                "gold": gold,
                "silver": silver,
                "bronze": bronze,
                "medals": medals
            }
            all_athletes.append(athlete_dict)

        return jsonify(all_athletes)
    except Exception as e:
        logger.error(f"Error in all-medal-winners API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/medals-tally/<int:selected_year>")
def total_medal_tally(selected_year):
    """ 
    Return the total number of medals won by all countries in the selected year
    
    Parameters:
    selected_year (int): Year to filter results by
    
    Returns:
    JSON: List of dictionaries containing medal data for the selected year
    """
    try:
        query = db.session.query(
            Athletes.Year,
            Athletes.Country,
            Athletes.Gold,
            Athletes.Silver,
            Athletes.Bronze,
            Athletes.Medals
        ).filter(Athletes.Year == selected_year)\
        .order_by(desc(Athletes.Medals))

        all_medals = []

        for year, country, gold, silver, bronze, total_medals in query.all():
            country_dict = {
                "year": year,
                "country": country,
                "gold": gold,
                "silver": silver,
                "bronze": bronze,
                "total_medals": total_medals
            }
            all_medals.append(country_dict)

        return jsonify(all_medals)
    except Exception as e:
        logger.error(f"Error in medals-tally API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/total-medals")
def total_medals():
    """ 
    Return the total number of medals won by all countries in Olympics held after 1980
    
    Returns:
    JSON: List of dictionaries containing medal data after 1980
    """
    try:
        query = db.session.query(
            Athletes.Year,
            Athletes.Country,
            Athletes.Medals
        ).filter(Athletes.Year >= 1980)\
        .order_by(Athletes.Year, desc(Athletes.Medals))
        
        all_country_medals = []

        for year, country, totalmedals in query.all():
            country_medals = {
                "year": year,
                "country": country,
                "total_medals": totalmedals
            }
            all_country_medals.append(country_medals)

        return jsonify(all_country_medals)
    except Exception as e:
        logger.error(f"Error in total-medals API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/host-countries")
def host_countries():
    """
    Return all host countries and their medal counts
    
    Returns:
    JSON: List of dictionaries containing medal data for host countries
    """
    try:
        query = db.session.query(
            Athletes.Year,
            Athletes.Country,
            Athletes.Host,
            Athletes.Gold,
            Athletes.Silver,
            Athletes.Bronze,
            Athletes.Medals
        ).filter(Athletes.Host == 1)\
        .order_by(Athletes.Year)

        hosts = []

        for year, country, host, gold, silver, bronze, medals in query.all():
            host_dict = {
                "year": year,
                "country": country,
                "gold": gold,
                "silver": silver,
                "bronze": bronze,
                "total_medals": medals
            }
            hosts.append(host_dict)

        return jsonify(hosts)
    except Exception as e:
        logger.error(f"Error in host-countries API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/country/<selected_country>")
def country_medals(selected_country):
    """
    Return the medals won by a specific country over the years
    
    Parameters:
    selected_country (str): Country to filter results by
    
    Returns:
    JSON: List of dictionaries containing medal data for the selected country
    """
    try:
        query = db.session.query(
            Athletes.Year,
            Athletes.Country,
            Athletes.Gold,
            Athletes.Silver,
            Athletes.Bronze,
            Athletes.Medals
        ).filter(Athletes.Country.ilike(f'%{selected_country}%'))\
        .order_by(Athletes.Year)

        country_data = []

        for year, country, gold, silver, bronze, medals in query.all():
            country_dict = {
                "year": year,
                "country": country,
                "gold": gold,
                "silver": silver,
                "bronze": bronze,
                "total_medals": medals
            }
            country_data.append(country_dict)

        return jsonify(country_data)
    except Exception as e:
        logger.error(f"Error in country medals API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/medals-tally/years_after_1960")
def total_medal_tally_year_after_1960():
    """ 
    Return the total medals won by all countries after 1960
    
    Returns:
    JSON: List of dictionaries containing medal data after 1960
    """
    try:
        query = db.session.query(
            Athletes.Year,
            Athletes.Country,
            Athletes.Gold,
            Athletes.Silver,
            Athletes.Bronze,
            Athletes.Medals
        ).filter(Athletes.Year >= 1960)\
        .order_by(Athletes.Year, desc(Athletes.Medals))

        all_medals = []

        for year, country, gold, silver, bronze, total_medals in query.all():
            country_dict = {
                "Year": year,
                "Nation": country,
                "Gold": gold,
                "Silver": silver,
                "Bronze": bronze,
                "Medals": total_medals
            }
            all_medals.append(country_dict)

        return jsonify(all_medals)
    except Exception as e:
        logger.error(f"Error in medals-tally-years-after-1960 API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/countries")
def get_countries():
    """
    Return a list of all countries in the dataset
    
    Returns:
    JSON: List of country names
    """
    try:
        query = db.session.query(distinct(Athletes.Country)).order_by(Athletes.Country)
        countries = [country[0] for country in query.all()]
        return jsonify(countries)
    except Exception as e:
        logger.error(f"Error in countries API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/years")
def get_years():
    """
    Return a list of all Olympic years in the dataset
    
    Returns:
    JSON: List of years
    """
    try:
        query = db.session.query(distinct(Athletes.Year)).order_by(Athletes.Year)
        years = [year[0] for year in query.all()]
        return jsonify(years)
    except Exception as e:
        logger.error(f"Error in years API: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Error handlers

# @app.errorhandler(404)
# def page_not_found(e):
#     """Handle 404 errors"""
#     return render_template('404.html'), 404

# @app.errorhandler(500)
# def server_error(e):
#     """Handle 500 errors"""
#     return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)