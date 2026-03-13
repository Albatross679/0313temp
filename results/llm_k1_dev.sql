SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city JOIN airport_service airport_service_2 JOIN city city_2 JOIN days days JOIN date_day date_day_1 WHERE flight.departure_time BETWEEN 0900 AND 0900 AND (     flight.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city.city_code AND city.city_name = 'BALtimore' )
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight WHERE from_airport = 'BOS' AND arrival_airport = 'SFO' AND stops = (     SELECT MAX(stops)     FROM flight     WHERE from_airport = 'BOS'     AND arrival_airport = 'SFO' );
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city_1 ON flight.from_airport = city_1.city_code AND city_1.city_name = 'PITTSBURGH' JOIN city city_2 ON flight.to_airport = city_2.city_code AND city_2.city_name = 'FORT WORTH' WHERE flight.departure_time BETWEEN 1000 AND 1900;
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service_1 ON flight.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'DENVER' AND flight.to_airport = airport_service_2.airport_code AND airport_service_2.city_code = 'SAN FRANCISCO' AND flight.flight_days = '2023-04-23' AND flight.departure_time BETWEEN 1800 AND 2200;
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT g.transport_type FROM ground_service g WHERE g.airport_code = 'PHL' AND g.transport_type = 'BUS' AND g.city_code = 'PHL' AND g.time >= 0 AND g.time <= 1200;
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT fare.fare_id FROM flight_fare fare JOIN flight flight ON fare.flight_id = flight.flight_id WHERE flight.from_airport = 'JFK'   AND flight.to_airport = 'LAX'   AND flight.departure_time BETWEEN '1800' AND '2200';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT aircraft.aircraft_code FROM aircraft JOIN flight_leg flight_leg ON aircraft.aircraft_code = flight_leg.aircraft_code JOIN flight flight ON flight_leg.flight_id = flight.flight_id WHERE flight.from_airport = 'BOS' AND flight.to_airport = 'SFO'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city JOIN airport_service airport_service_2 JOIN city city_2 JOIN days days JOIN date_day date_day_1 WHERE flight.departure_time BETWEEN 1300 AND 1700 AND (     flight.from_airport = airport_service.airport_code     AND airport_service.city_code = city.city_code     AND city.city_name = 'CHARLOTTE' )
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT flight_id FROM flight WHERE departure_time BETWEEN 1800 AND 2200 AND from_airport = 'DAL' AND class_type = 'FIRST CLASS' AND (     (to_airport = 'BAL' AND departure_airline = 'AA')     OR (to_airport = 'BWI' AND departure_airline = 'BW') );
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
The provided SQL query does not contain any information regarding "iah", so I cannot extract the requested data from the provided context.
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city_1 ON flight.from_airport = city_1.city_code JOIN city city_2 ON flight.to_airport = city_2.city_code WHERE flight.departure_time BETWEEN '2023-08-18 18:00:00' AND '2023-08-18 22:00:00'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight_1 INNER JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'NYC' AND flight_1.to_airport = airport_service_2.airport_code AND airport_service_2.city_code = 'MIA' AND flight_1.flight_days = days_1.days_code AND days_1.day_name = 'FRIDAY'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT COUNT(*) FROM flight WHERE departure_time BETWEEN 1800 AND 2200 AND from_airport = 'PHOENIX' AND flight_days = 23 AND airline_code = 'UA';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT g.transport_type FROM ground_service g WHERE g.airport_code = 'PITTSBURGH'   AND g.transport_type = 'TAXI'   AND EXISTS (     SELECT 1     FROM airport_service AS as1     WHERE as1.airport_code = g.airport_code       AND as1.transport_type = 'TAXI'       AND as1.city_code = 'PITTSBURGH'   );
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
The provided SQL query does not contain any information regarding what ff means, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service_1 ON flight.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'BALtimore' AND flight.to_airport = airport_service_2.airport_code AND airport_service_2.city_code = 'Dallas' AND flight.flight_days = '2023-04-23'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city_1 ON flight.from_airport = city_1.city_code AND city_1.city_name = 'PITTSBURGH' JOIN city city_2 ON flight.to_airport = city_2.city_code AND city_2.city_name = 'BOSTON' WHERE flight.departure_time BETWEEN 1200 AND 1900;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
The provided SQL query does not contain any information related to ground transportation in Boston, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service.transport_type FROM airport_service INNER JOIN ground_service ON airport_service.airport_code = ground_service.airport_code WHERE airport_service.city_code = 'PITTSBURGH' AND ground_service.transport_type = 'TAXI'
SELECT aircraft_code FROM aircraft WHERE basic_type = 'F28';
SELECT DISTINCT car.car_code FROM flight f JOIN flight_leg fl ON f.flight_id = fl.flight_id JOIN car c ON fl.car_id = c.car_id WHERE f.departure_time BETWEEN '2023-04-23 18:00:00' AND '2023-04-23 22:00:00' AND c.car_type = 'SEDAN' AND c.rental_agency = 'XYZ';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city_1 ON flight.from_airport = city_1.city_code AND city_1.city_name = 'ATLANA' JOIN city city_2 ON flight.to_airport = city_2.city_code AND city_2.city_name = 'WASHINGTON' WHERE flight.departure_time > 1500;
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service_1 ON flight.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'LAS VEGAS' AND flight.to_airport = airport_service_2.airport_code AND airport_service_2.city_code = 'NEW YORK' AND flight.flight_days = '2023-04-23';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service.transport_type FROM airport_service INNER JOIN ground_service ON airport_service.airport_code = ground_service.airport_code WHERE airport_service.city_code = 'SFO' AND ground_service.transport_type = 'BUS'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT fare.round_trip_cost FROM fare WHERE from_airport = 'PITTSBURGH' AND flight_id = (     SELECT flight_id     FROM flight     WHERE departure_time BETWEEN 1800 AND 2200     AND (         departure_airline = 'LIAMINE'         AND departure_airport = 'PITTSBURGH'     ) );
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city_1 ON flight.from_airport = city_1.city_code AND city_1.city_name = 'CLEVELAND' JOIN city city_2 ON flight.to_airport = city_2.city_code AND city_2.city_name = 'MIAMI' WHERE flight.arrival_time < '16:00'
SELECT class_of_service FROM class_of_service WHERE airline_code = 'LH' AND booking_class IN ('BUSINESS', 'FIRST');
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city_1 ON flight.from_airport = city_1.city_code AND city_1.city_name = 'OAKLAND' JOIN city city_2 ON flight.to_airport = city_2.city_code AND city_2.city_name = 'PHILADELPHIA' WHERE flight.arrival_time BETWEEN 1500 AND 1800;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT airport_service.minutes_distant FROM airport_service WHERE airport_service.airport_code = 'DFW' AND airport_service.city_code = 'DFW' AND airport_service.direction = 'outbound' AND distance(airport_service.airport_location, 'DFW') > 0;
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT ground_service.transport_type FROM airport_service INNER JOIN ground_service ON airport_service.airport_code = ground_service.airport_code WHERE airport_service.city_code = 'SFO' AND ground_service.transport_type = 'BUS';
SELECT DISTINCT flight_id
SELECT DISTINCT ground_service.transport_type FROM airport_service INNER JOIN ground_service ON airport_service.airport_code = ground_service.airport_code WHERE airport_service.city_code = 'SANFRANCISCO'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
The provided SQL query does not contain any information regarding "ewr", so I cannot extract the requested data from the provided context.
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service_1 ON flight.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'DENVER' AND flight.to_airport = airport_service_2.airport_code AND airport_service_2.city_code = 'BALtimore' AND flight.flight_days = '2023-04-23' AND flight.airline_code = 'UA'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT car.car_id FROM car WHERE city = 'BALtimore';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city JOIN airport_service airport_service_2 JOIN days days JOIN date_day date_day_1 WHERE flight.departure_time BETWEEN 0 AND 900 AND (     flight.from_airport = airport_service.airport_code     AND airport_service.city_code = city.city_code     AND city.city_name = ' atlanta' )
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN flight_stop flight_stop ON flight.flight_id = flight_stop.flight_id JOIN city city ON flight_stop.stop_airport = city.city_code JOIN city city2 ON flight_stop.arrival_airport = city2.city_code WHERE city.city_name = 'BOSTON' AND flight_stop.stop_days > 3
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'OAKLAND' AND airport_service_1.direction = 'outbound' AND flight_1.departure_time BETWEEN '08:00:00' AND '12:00:00'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL query does not contain any information regarding costs of rental cars, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
The provided SQL query does not contain any information regarding the code "y", so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city_1 ON flight.from_airport = city_1.city_code AND city_1.city_name = 'WASHINGTON' JOIN airport_service airport_service_2 ON flight.to_airport = airport_service_2.airport_code AND airport_service_2.city_code = 'DENVER' WHERE flight.departure_time BETWEEN 1800 AND 2200;
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city_1 ON flight.from_airport = city_1.city_code AND city_1.city_name = 'PITTSBURGH' JOIN airport_service airport_service_2 ON flight.to_airport = airport_service_2.airport_code AND airport_service_2.city_code = 'ATLANTA' WHERE flight.departure_time BETWEEN 1800 AND 2200;
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city JOIN airport_service airport_service_2 JOIN city city_2 JOIN days days JOIN date_day date_day_1 WHERE flight.departure_time BETWEEN 1800 AND 2200 AND (     flight.from_airport = airport_service.airport_code     AND airport_service.city_code = city.city_code     AND city.city_name = ' atlanta' )
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT COUNT(DISTINCT flight_id) FROM flight WHERE departure_time BETWEEN DATE_SUB(NOW(), INTERVAL 1 DAY) AND NOW() AND airline_code = 'UA' AND flight_days = (SELECT days_code FROM days WHERE day_name = 'WEDNESDAY' AND month_number = 4 AND day_number = 23);
SELECT DISTINCT flight_id
SELECT DISTINCT aircraft.aircraft_code FROM aircraft WHERE airline_code = (     SELECT airline_code     FROM airline     WHERE airline_name = 'CANADIAN AIRLINES' );
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service_1 ON flight.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'DENVER' AND flight.to_airport = airport_service_2.airport_code AND airport_service_2.city_code = 'PITTSBURGH' AND airport_service_2.city_code = 'ATLANTA' AND flight.flight_days = '2023-04-23';
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service_1 ON flight.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'BALtimore' AND airport_service_1.city_name = 'DENVER' JOIN airport airport_service_2 ON flight.to_airport = airport_service_2.airport_code AND airport_service_2.city_code = 'SAN FRANCISCO' AND airport_service_2.city_name = 'SAN FRANCISCO';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight WHERE departure_time BETWEEN 1800 AND 2200 AND (     FROM_airport = 'LOVEFIELD'     OR FROM_airport = 'LAX'     OR FROM_airport = 'SFO' );
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service_1 ON flight.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'BOS' AND flight.departure_time BETWEEN 0800 AND 1200 JOIN city city_1 ON airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'BOSTON';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT COUNT(*) FROM flight_stop WHERE stop_days = 1 AND aircraft_code = '734';
The provided SQL query does not contain any information regarding "ewr", so I cannot extract the requested data from the provided context.
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries do not contain any information related to ground transportation in Denver, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT g.transport_type FROM ground_service g WHERE g.airport_code = 'SFO' AND g.transport_type = 'BUS';
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city JOIN airport_service airport_service_2 JOIN city city_2 JOIN days days JOIN date_day date_day_1 WHERE flight.departure_time < 1200 AND (     flight.from_airport = airport_service.airport_code     AND airport_service.city_code = city.city_code     AND city.city_name = 'DENVER' )
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
The provided SQL query does not contain any information regarding limousine services, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_id FROM flight WHERE from_airport = 'BALtimore' AND departure_time BETWEEN 1800 AND 2200;
SELECT DISTINCT flight_1.flight_id
SELECT fare.round_trip_cost FROM fare WHERE from_airport = 'DENVER'   AND to_airport = 'PITTSBURGH'   AND round_trip_required = 'YES';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT fare.fare_id FROM fare WHERE from_airport = 'BOS' AND to_airport = 'PHL'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service_1 ON flight.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'ATL' AND flight.to_airport = airport_service_2.airport_code AND airport_service_2.city_code = 'PIT' AND flight.flight_days = '2023-04-23';
SELECT DISTINCT flight_id
SELECT DISTINCT airport_code FROM airport WHERE country_name = 'USA' AND state_code = 'DC';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT ground_service.transport_type FROM airport_service INNER JOIN ground_service ON airport_service.airport_code = ground_service.airport_code WHERE airport_service.city_code = 'BOS' AND ground_service.transport_type = 'BUS';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city_1 ON flight.from_airport = city_1.city_code AND city_1.city_name = 'PITTSBURGH' JOIN city city_2 ON flight.to_airport = city_2.city_code AND city_2.city_name = 'ATLANTA' WHERE flight.departure_time BETWEEN 1800 AND 2200;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT fare.round_trip_cost FROM fare WHERE from_airport = 'OAKLAND'   AND to_airport = 'ATLANTA'   AND class_of_service = 'FIRST CLASS';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT ground_service.transport_type FROM airport_service INNER JOIN ground_service ON airport_service.airport_code = ground_service.airport_code;
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT class_description FROM class_of_service WHERE airline_code = 'TWA';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT airport_service.minutes_distant FROM airport_service WHERE airport_service.airport_code = 'SFO'
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id FROM flight WHERE departure_time BETWEEN (SELECT end_time FROM time_interval WHERE period = 'DAY' AND end_time >= 2200) AND from_airport = 'LOVEFIELD' ORDER BY departure_time DESC;
SELECT DISTINCT flight_id FROM flight WHERE arrival_time BETWEEN 1800 AND 2200 AND from_airport = 'GENERAL MITCHELL INTERNATIONAL AIRPORT'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT ground_service.transport_type FROM airport_service INNER JOIN ground_service ON airport_service.airport_code = ground_service.airport_code WHERE airport_service.city_code = 'MINneapolis'
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT f.flight_id FROM flight f JOIN fare f ON f.flight_id = f.flight_id JOIN class_of_service c ON f.booking_class = c.booking_class WHERE c.class_description = 'Economy' AND f.from_airport = 'DAL' AND f.to_airport = 'BAL'
SELECT DISTINCT airport_service.airport_code FROM airport_service WHERE airport_service.city_code = 'TAMPA' AND airport_service.direction = 'outbound';
SELECT DISTINCT flight_id FROM flight WHERE departure_date = CURDATE()
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT airport_service.transport_type FROM airport_service WHERE airport_service.airport_code = 'PHL' AND airport_service.direction = 'outbound' AND airport_service.city_code = 'PHL';
The provided SQL query does not contain any information related to rental cars in Washington DC, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT distance FROM airport WHERE airport_code = 'DAL' AND city_name = 'DALLAS';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT fare.fare_id FROM fare WHERE flight_id = (     SELECT flight_id     FROM flight     WHERE departure_time BETWEEN 1800 AND 2200     AND from_airport = 'DAL'     AND to_airport = 'SFO' );
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city_1 ON flight.from_airport = airport_service.airport_code AND airport_service.city_code = city_1.city_code AND city_1.city_name = 'INDIANAPOLIS' JOIN city city_2 ON flight.to_airport = airport_service.airport_code AND airport_service.city_code = city_2.city_code AND city_2.city_name = 'SAN DIEGO';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
The provided SQL query does not contain any information regarding the cost of transportation from the Atlanta airport to downtown, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
