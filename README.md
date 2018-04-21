

Description:
  Accepts a user query and searches a database for NFL quarterback passing
  statistic. Based on the input, the user can see a variety of statistics for a
  given quarterback. When choosing a single statistic to view, a bar chart from
  Plotly will come up in the browser with the years on the x-axis and statistic
  values on the y-axis. The user also has the option of searching for two
  quarterbacks and comparing their stats using a double bar chart.

Commands:
  list <QBname> <stat>
  compare <QBname> and <QBname> <stat>

  Input for <QBname> must be capitalized.
  Input options for <stat> include:
                                        team
                                        age
                                        record
                                        completions
                                        passyards
                                        touchdowns
                                        interceptions
                                        rating
                                        stats

API Source: https://api.sportradar.us/nfl-ot2/league/hierarchy.json?api_key=MY_API_KEY
Web Scraping Source: https://www.pro-football-reference.com/players/qbindex.htm


My code is structured to first initiate the database using init_db(). Then, the
Teams table populates itself because that doesn't depend on user input. However,
to populate the SeasonalStats and PlayerInfo tables, user input is required. A
user passes in their query and the database will subsequently populate itself
using web scraped data. From there, the program will list the data the user
specified in their query using list_info function, which can manipulate data in
the database.
