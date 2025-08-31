
make sure you have a folder ./26-Aug-25 with gpx files in it first
```
python consolidator.py --input ./26-Aug-25 --output Aug26.gpx --filter-date 2025-08-26 --start-time 06:00 --end-time 20:00
```

# weird unresolved issues
gpx has to have waypoints, routes and then tracks but the names of all of these have to be unique despite people possibly entering the same name for any of the above on any of their devices. It means you have to iterate through them, rename them with unique names as required and you have to have an intermediate memory object (you can't just build your new xml as you go). There is probably a way to do this but I haven't done it so the result is that you iterate through a file, add to your intermediate memory objects and then iterate through those to build your xml. It seems silly. There should be a way to insert items. as you build your new xml doc. 

also there should only be one naming function but I have two in there because we might have different conventions for naming tracks and waypoints. 

# TODO

- [x] consolidate routes too
- [x] test waypoints consolidation (it should work ...) 
- [ ] track colours would be nice
- [ ] it would be cool to have an algo to paint tracks from routes

# features
- filters tracks on time and date or just consolidates them