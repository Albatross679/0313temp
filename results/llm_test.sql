SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name IN ('DENVER', 'PHILADELPHIA')
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name IN ('ST. LOUIS', 'PHILADELPHIA', 'DENVER');
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = 'BWI' AND ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'BOSTON';
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = 'BWI' AND ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'BOSTON';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, airport_service airport_service_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'DETROIT'
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries are already written and ready to execute. They retrieve flight information based on the specified criteria.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, airport_service airport_service_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name IN ('DENVER', 'ATLANTA', 'BOSTON', 'INDIANAPOLIS');
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT flight_id FROM flight WHERE from_airport = 'CLEVELAND' AND departure_time > 1700 AND (flight_days = 'W' AND day_name = 'WEDNESDAY')
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city ON flight.from_airport = airport_service.airport_code JOIN airport airport ON airport.airport_code = city.city_code WHERE flight.departure_time > 1700;
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city ON flight.from_airport = airport_service.airport_code JOIN airport airport ON airport.airport_code = city.city_code WHERE flight.departure_time > 1700;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, airport_service airport_service_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'DENVER';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'SALT LAKE CITY';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, airport_service airport_service_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name IN ('DENVER', 'BOSTON', 'ATLANTA', 'PHOENIX');
SELECT DISTINCT flight_1.flight_id
SELECT flight_id FROM flight WHERE from_airport = 'OAKLAND' AND departure_time < 900 AND flight_days = 4 AND EXISTS (   SELECT 1   FROM flight_stop   WHERE flight_id = flight.flight_id   AND arrival_time >= 900 );
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airport_1.airport_code FROM airport airport_1, airport_service airport_service_1, city city_1 WHERE airport_1.airport_code = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name IN ('DENVER', 'BALTIMORE');
SELECT DISTINCT airport_1.airport_code
SELECT DISTINCT airport_1.airport_code, airport_1.airport_name, airport_1.airport_location, airport_1.state_code, airport_1.country_name, airport_1.time_zone_code, airport_1.minimum_connect_time
SELECT DISTINCT airport_1.airport_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airport_1.airport_code
SELECT DISTINCT airport_1.airport_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP';  SELECT DISTINCT airport_1.airport_code FROM airport airport_1 WHERE airport_1.airport_code = 'EWR';  SELECT DISTINCT airport_1.airport_code FROM airport airport_1 WHERE airport_1.airport_code = 'MIA';  SELECT * FROM flight;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT aircraft_1.basic_type
SELECT DISTINCT aircraft_1.aircraft_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name IN ('NEW YORK', 'PITTSBURGH', 'TAMPA') AND ground_service_1.transport_type = 'RENTAL CAR';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code = 'QO';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'US';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code = 'F' OR fare_basis_1.fare_basis_code = 'FN';
The provided SQL queries do not contain any information related to the meaning of fare codes, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code = 'Y';
SELECT DISTINCT restriction_1.restriction_code FROM restriction restriction_1 WHERE restriction_1.restriction_code = 'AP/57';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'DL';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code = 'Q';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code = 'Q';
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code = 'Q';
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code = 'Q';
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code = 'Q';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP'  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP'  SELECT DISTINCT airline_1.airline_code FROM airline airline_1;
SELECT DISTINCT ground_service_1.transport_type
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 JOIN airport airport_1 ON ground_service_1.airport_code = airport_1.airport_code JOIN airport_service airport_service_1 ON airport_service_1.airport_code = airport_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'LAS VEGAS'
The provided SQL queries are already written and ready to execute. They are designed to retrieve flight information between various airports.
The provided SQL queries are already written and ready to execute. They are designed to retrieve flight information between various airports.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'US' OR airline_1.airline_name = 'USAIR' OR airline_1.airline_code = 'FF';
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'US' OR airline_1.airline_name = 'USAIR';
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'US' OR airline_1.airline_name = 'USAIR';
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'US' OR airline_1.airline_name = 'USAIR';
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'US' OR airline_1.airline_name = 'USAIR';
SELECT DISTINCT flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP'  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP'  SELECT DISTINCT airline_1.airline_code FROM airline airline_1;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP'  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP'  SELECT DISTINCT airline_1.airline_code FROM airline airline_1;
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 INNER JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name IN ('PHOENIX', 'DENVER', 'BALTIMORE');
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type, ground_service_1.ground_fare FROM ground_service ground_service_1 JOIN airport airport_1 ON ground_service_1.airport_code = airport_1.airport_code WHERE airport_1.airport_code = 'DFW'
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code = 'F' OR fare_basis_1.fare_basis_code = 'FN';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT restriction_1.restriction_code FROM restriction restriction_1 WHERE restriction_1.restriction_code = 'AP/57' -- Other queries using the same pattern
The provided SQL queries do not contain any information related to the meaning of fare codes, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1;
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1;
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1;
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP'  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'HP'  SELECT DISTINCT airline_1.airline_code FROM airline airline_1;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airport_1.airport_code FROM airport airport_1, airport_service airport_service_1, city city_1 WHERE airport_1.airport_code = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'NEW YORK';
SELECT DISTINCT airport_1.airport_code FROM airport airport_1 JOIN airport_service airport_service_1 ON airport_1.airport_code = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'NEW YORK';
SELECT DISTINCT airport_1.airport_code FROM airport airport_1 JOIN airport_service airport_service_1 ON airport_1.airport_code = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'NEW YORK';
The provided SQL queries do not contain any information related to airports in Baltimore, New York, or Los Angeles, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT airport_1.airport_code
The provided SQL queries do not contain any information related to airports in Baltimore, New York, or Los Angeles, so I am unable to extract the requested data from the provided context.
The provided SQL queries do not contain any information related to airports in Baltimore, New York, or Los Angeles, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT airport_1.airport_code FROM airport airport_1 JOIN airport_service airport_service_1 ON airport_1.airport_code = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'BALTIMORE';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1, airport airport_2 WHERE flight_1.from_airport = airport_1.airport_code AND airport_1.airport_code = 'LGA' AND flight_1.to_airport = airport_2.airport_code AND airport_2.airport_code = 'BUR'
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport airport_1 ON flight_1.from_airport = airport_1.airport_code JOIN airport airport_2 ON airport_1.airport_code = airport_2.airport_code WHERE airport_1.airport_code = 'LGA' AND airport_2.airport_code = 'JFK';
SELECT DISTINCT flight_id FROM flight WHERE from_airport = 'ONTARIO' AND to_airport = 'ORLANDO'
SELECT DISTINCT flight_id FROM flight WHERE from_airport = 'ONTARIO' AND to_airport = 'ORLANDO'
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT aircraft_1.aircraft_code
SELECT DISTINCT class_of_service_1.booking_class FROM class_of_service class_of_service_1 WHERE class_of_service_1.booking_class = 'Q';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries are already written and ready to execute. They are designed to retrieve specific information from the database based on the provided conditions.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'BALTIMORE';
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 INNER JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name IN ('BALTIMORE', 'DETROIT', 'ATLANTA');
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
The provided SQL queries do not contain any information related to coach flights, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'DALLAS' AND flight_1.arrival_time > 1201;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT count( DISTINCT flight_1.flight_id ) FROM flight flight_1, airport_service airport_service_1, city city_1 WHERE flight_1.airline_code = 'DL'   AND flight_1.from_airport = airport_service_1.airport_code   AND airport_service_1.city_code = city_1.city_code   AND city_1.city_name = 'WASHINGTON' GROUP BY flight_1.flight_id;
SELECT count( DISTINCT flight_1.flight_id ) FROM flight flight_1, airport_service airport_service_1, city city_1 WHERE flight_1.airline_code = 'DL'   AND flight_1.from_airport = airport_service_1.airport_code   AND airport_service_1.city_code = city_1.city_code   AND city_1.city_name = 'WASHINGTON' GROUP BY flight_1.flight_id;
The provided SQL queries do not contain any information related to the number of airports or flights leaving from specific locations, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 JOIN city city_1 ON flight_1.to_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'DENVER';
SELECT DISTINCT city_1.city_code FROM city city_1, airport_service airport_service_1, flight flight_1 WHERE city_1.city_code = airport_service_1.city_code AND airport_service_1.airport_code = flight_1.from_airport AND flight_1.airline_code = 'UA' AND 1 = 1;
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.to_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'DENVER'
The provided SQL queries are already written and ready to execute. They retrieve information about flights based on the specified criteria.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.aircraft_code = 'D9S';
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.aircraft_code = 'M80';
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.aircraft_code = 'D9S';
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code JOIN airport_service airport_service_2 ON flight_1.to_airport = airport_service_2.airport_code JOIN city city_2 ON airport_service_2.city_code = city_2.city_code;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.capacity = (     SELECT MAX(aircraft_1.capacity)     FROM aircraft aircraft_1     WHERE 1 = 1 );
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.manufacturer = 'BOEING' AND aircraft_1.basic_type = '767';
SELECT DISTINCT aircraft_1.aircraft_code, aircraft_1.capacity
SELECT DISTINCT aircraft_1.aircraft_code, aircraft_1.capacity
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.capacity = (     SELECT MAX(aircraft_1.capacity)     FROM aircraft aircraft_1     WHERE 1 = 1 );
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.aircraft_code = 'M80';
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 JOIN flight flight_1 ON airline_1.airline_code = flight_1.airline_code JOIN airport_service airport_service_1 ON flight_1.to_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'DENVER';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 JOIN flight flight_1 ON airline_1.airline_code = flight_1.airline_code JOIN airport_service airport_service_1 ON flight_1.to_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'DENVER';
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.to_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE flight_1.airline_code = 'CO' AND flight_1.arrival_time > 2100 AND city_1.city_name = 'CHICAGO';
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.manufacturer = 'BOEING' AND aircraft_1.basic_type = '767';
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.aircraft_code = '73S';  SELECT DISTINCT airport_1.airport_code FROM airport airport_1 WHERE airport_1.airport_code = 'MCO';  SELECT DISTINCT airport_1.airport_code FROM airport airport_1 WHERE airport_1.airport_code = 'EWR';  SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1;
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.capacity = (     SELECT MAX(aircraft_1.capacity)     FROM aircraft aircraft_1     WHERE 1 = 1 );
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.manufacturer = 'BOEING' AND aircraft_1.basic_type = '767';
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.basic_type = '737' AND aircraft_1.manufacturer = 'BOEING';
The provided code snippets do not contain any information related to the number of passengers that can fit on a specific aircraft, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.basic_type = '757';
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 WHERE flight_1.airline_code = 'TW' AND flight_1.flight_number = 539;
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 WHERE flight_1.airline_code = 'TW' AND flight_1.flight_number = 539;
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.aircraft_code = 'M80';
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.aircraft_code = '733';
SELECT DISTINCT aircraft_1.aircraft_code
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.capacity = (     SELECT MAX(aircraft_1.capacity)     FROM aircraft aircraft_1     WHERE 1 = 1 );
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.to_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE flight_1.airline_code = 'CO' AND flight_1.arrival_time > 2100 AND city_1.city_name = 'CHICAGO';
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 JOIN equipment_sequence equipment_sequence_1 ON aircraft_1.aircraft_code = equipment_sequence_1.aircraft_code JOIN flight flight_1 ON equipment_sequence_1.aircraft_code_sequence = flight_1.aircraft_code_sequence WHERE flight_1.arrival_time BETWEEN 19 AND 21;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type
SELECT DISTINCT flight_1.flight_id
The provided code snippet does not contain any information related to the questions provided, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'WASHINGTON';
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name IN ('WASHINGTON', 'DENVER', 'DALLAS', 'NEW YORK CITY');
The provided context does not contain any information regarding ground transportation from LGA into New York City, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type
SELECT DISTINCT flight_1.flight_id
SELECT count( DISTINCT flight_1.flight_id )
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id FROM flight JOIN airport_service airport_service JOIN city city ON airport_service.airport_code = city.city_code JOIN airport_service airport_service_2 ON airport_service.airport_code = airport_service_2.airport_code WHERE city.city_name = 'BURBANK' AND airport_service_2.airport_code = 'DENVER'
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS'  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS'  SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'AS';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code
The provided SQL queries are already written and ready to execute. They retrieve the requested information from the database.
SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1 WHERE flight_1.from_airport = airport_1.airport_code AND airport_1.airport_code = 'MKE';
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code JOIN city city_2 ON flight_1.to_airport = city_2.city_code WHERE flight_1.airline_code = 'NW' AND flight_1.departure_time < 1200
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries are already written and ready to execute. They retrieve the flight information based on the specified criteria.
SELECT DISTINCT flight_1.flight_id
The provided SQL queries are already translated from the given questions. They return the flight IDs that meet the specified criteria for each question.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries do not contain any information regarding the specific aircraft used for the American flight leaving at 419pm, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, airport_service airport_service_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name IN ('BOSTON', 'PHL', 'LAS VEGAS');
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1 WHERE ground_service_1.transport_type = 'LIMOUSINE' AND ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = 'PIT';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries are already written and translated. They are designed to retrieve specific flights that meet the specified criteria.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 INNER JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'SAN DIEGO' INNER JOIN city city_2 ON flight_1.to_airport = city_2.city_code AND city_2.city_name = 'PHOENIX';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airport_1.airport_code FROM airport airport_1, airport_service airport_service_1, city city_1 WHERE airport_1.airport_code = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'WESTCHESTER COUNTY';
SELECT DISTINCT flight_id
SELECT DISTINCT airport_1.airport_code FROM airport airport_1, airport_service airport_service_1, city city_1 WHERE airport_1.airport_code = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'NEW YORK';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
