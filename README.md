# Santa Route Optimization Mini Project

This project contains a Python app that calculates a route for delivering Santa's presents to children under consideration of technical limitations of the sleigh (maximal weight, maximal volume, speed, time per stop). Santa's basis is the north pole. Currently, the goal is to deliver all presents from 22 to 7 o'clock, i.e., in 7 hours. Naughty children will get a piece of coal instead of a present.

## Input
Input will be three semicolon-separated CSVs (decimal delimiter is the comma):
- children: CSV with columns "child" (ID), "latitude", "longitude", "wish" (the present's ID) and "naughty" (0 indicating not naughty)
- articles: CSV with columns "article" (the present's ID), "weight", "volume". Article with ID 0 corresponds to coal.
- specifications: CSV with columns "meta data", "value". "Meta data" has fields "maximum weight", "maximum volume", "speed (km/h)", "time per stop (min)"

## Output
The output is a CSV (semicolon-separed) that represents the routes and reloading of the sleigh as we cannot load more presents as said in the specifications. The CSV has the following format:
- columns: "stop", "article", "pieces"
- 0 in columns "stop" indicates a reloading. Reloading needs to fill the columns "article" with the article ID and "pieces" with the number of the reloaded article. Reloaded articles must not violate the sleigh restrictions. In "pieces" only integer values are allowed.
- other numbers in "stop" indicate a delivery and have NULL values in the columns "article" and "pieces"
