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
SELECT DISTINCT state_1.state_code FROM state state_1 WHERE state_1.state_code = 'ASD';
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.departure_time
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'PHILADELPHIA' AND flight_1.arrival_time >= 1600 AND flight_1.arrival_time <= 1700;
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare.fare_id FROM flight flight INNER JOIN fare fare ON fare.flight_id = flight.flight_id WHERE flight.from_airport = 'ORDH'   AND flight.to_airport = 'MCI'   AND flight.departure_time >= '18:00:00'   AND flight.departure_time <= '19:00:00'   AND fare.fare_basis_code = 'UA'
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'DENVER' AND flight_1.departure_time > 500
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT aircraft_1.aircraft_code
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code AND airport_service_1.city_code = 'DENVER' AND airport_service_1.city_name = 'SAN FRANCISCO' AND flight_1.arrival_time = 1700;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'PHILADELPHIA' AND day_name = 'WEDNESDAY';
SELECT DISTINCT flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'OAKLAND';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id FROM flight flight JOIN airport_service airport_service JOIN city city JOIN airport_service airport_service2 JOIN city city2 WHERE flight_from = airport_service.airport_code AND airport_service.city_code = city.city_code AND city.city_name = 'PITTSBURGH' AND flight_to = airport_service2.airport_code AND airport_service2.city_code = city2.city_code AND city2.city_name = 'SAN FRANCISCO';
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_id
SELECT DISTINCT ground_service_1.ground_fare FROM ground_service ground_service_1 JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'DALLAS' AND ground_service_1.transport_type = 'RENTAL CAR';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT aircraft_1.aircraft_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT fare_id
SELECT fare_1.fare_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided code does not contain any information related to the terms "ewr", "us", "ea", or "iah", so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT count( DISTINCT flight_1.flight_id )
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id FROM fare fare_1
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 JOIN airport airport_1 ON ground_service_1.airport_code = airport_1.airport_code JOIN city city_1 ON airport_1.airport_code = city_1.city_code WHERE city_1.city_name = 'BOSTON';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'CO';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT count( DISTINCT flight_1.flight_id ) FROM flight flight_1, airport_service airport_service_1, city city_1 WHERE flight_1.airline_code = 'UA'   AND flight_1.from_airport = airport_service_1.airport_code   AND airport_service_1.city_code = city_1.city_code   AND city_1.city_name = 'SAN FRANCISCO';
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.ground_fare FROM ground_service ground_service_1, airport airport_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code   AND airport_1.airport_code = 'PIT'   AND ground_service_1.city_code = city_1.city_code   AND city_1.city_name = 'PITTSBURGH';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
The provided code does not contain any information related to the terms "ea", "us", "hou", or "ff", so I am unable to extract the requested data from the provided context.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries do not contain any information related to the earliest flight from Pittsburgh to San Francisco, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT state_1.state_code FROM state state_1 WHERE state_1.state_code = 'ASD';  SELECT DISTINCT airport_1.airport_code FROM airport airport_1 WHERE airport_1.airport_code = 'EWR';  SELECT DISTINCT airport_1.airport_code FROM airport airport_1 WHERE airport_1.airport_code = 'BUR';  SELECT DISTINCT state_1.state_code FROM state state_1;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name IN ('CHICAGO', 'ST. PETERSBURG', 'BOSTON');
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1 WHERE flight_1.to_airport = airport_1.airport_code AND airport_1.airport_code = 'MKE';
SELECT DISTINCT airport_1.airport_code FROM airport airport_1, flight flight_1 WHERE airport_1.airport_code = flight_1.to_airport AND flight_1.airline_code = 'CP' AND 1 = 1;
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = 'PIT'
SELECT DISTINCT aircraft_1.aircraft_code FROM aircraft aircraft_1 WHERE aircraft_1.aircraft_code = '733';
SELECT DISTINCT ground_service_1.transport_type
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code IN ('QW', 'QX', 'QO', '');
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = 'BOS' AND ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'BOSTON';
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT state_1.state_code FROM state state_1 WHERE state_1.state_code = 'ASD';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id, class_of_service_1.booking_class
SELECT DISTINCT ground_service_1.transport_type
SELECT DISTINCT flight_1.flight_id
The provided SQL queries all return the value of the `fare_basis_code` column from the `fare_basis` table where the `fare_basis_code` column is equal to 'QO'.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id FROM fare fare_1 INNER JOIN flight_fare flight_fare_1 ON fare_1.fare_id = flight_fare_1.fare_id INNER JOIN flight flight_1 ON flight_fare_1.flight_id = flight_1.flight_id INNER JOIN airline airline_1 ON flight_1.airline_code = airline_1.airline_code WHERE airline_1.airline_name = 'DL' AND flight_1.flight_number = 746;
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries do not contain any information related to Lufthansa, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT aircraft_1.aircraft_code
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 JOIN city city_1 ON flight_1.to_airport = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'PITTSBURGH' AND (flight_1.arrival_time >= 1200 AND flight_1.arrival_time <= 1600);
SELECT DISTINCT fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airport_service_1.miles_distant FROM airport_service airport_service_1, city city_1 WHERE airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'PITTSBURGH';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport airport_1 ON flight_1.from_airport = airport_1.airport_code JOIN airport airport_2 ON flight_1.to_airport = airport_2.airport_code WHERE airport_1.airport_code = 'DAL'
SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1 WHERE flight_1.from_airport = airport_1.airport_code AND airport_1.airport_code = 'DAL';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code   AND airport_1.airport_code = 'BWI'   AND ground_service_1.city_code = city_1.city_code   AND city_1.city_name = 'BALTIMORE';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'SAN FRANCISCO';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT airport_1.airport_code FROM airport airport_1 WHERE airport_1.airport_code = 'EWR' -- Other questions can be written here using the same pattern
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT city_1.city_code
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'BALTIMORE' AND ground_service_1.transport_type = 'RENTAL CAR';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries are already translated from the given question. They select distinct flight IDs that meet the specified criteria for each question.
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT days_1.day_name FROM days days_1 WHERE days_1.days_code = 'SA';  SELECT DISTINCT days_1.day_name FROM days days_1 WHERE days_1.days_code = 'SA';  SELECT DISTINCT airport_1.airport_code FROM airport airport_1 WHERE airport_1.airport_code = 'MCO';  SELECT DISTINCT days_1.day_name FROM days days_1;
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 JOIN airport airport_1 ON ground_service_1.airport_code = airport_1.airport_code JOIN city city_1 ON airport_1.airport_code = city_1.city_code WHERE city_1.city_name IN ('ORLANDO', 'TORONTO', 'CHICAGO')
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries do not contain any information regarding the specific aircraft used on any particular flight, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 INNER JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name IN ('DALLAS', 'OAKLAND', 'DENVER', 'SEATTLE');
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
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 INNER JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name IN ('BOSTON', 'DALLAS', 'DENVER') AND ground_service_1.transport_type = 'RENTAL CAR';
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 INNER JOIN flight flight_1 ON airline_1.airline_code = flight_1.airline_code INNER JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code INNER JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'DENVER';
SELECT DISTINCT fare_id
SELECT DISTINCT airline_1.airline_code
SELECT fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.departure_time, flight_1.arrival_time
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL code selects the distinct fare basis codes from the fare_basis table where the fare basis code is equal to 'QX', 'QO', or 'QX'.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT aircraft_1.aircraft_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'DL'
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name IN ('TORONTO', 'SALT LAKE CITY', 'CHICAGO', 'SAN FRANCISCO');
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_basis_1.fare_basis_code FROM fare_basis fare_basis_1 WHERE fare_basis_1.fare_basis_code = 'YN';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_id
SELECT count( DISTINCT flight_1.flight_id )
SELECT DISTINCT flight_1.flight_id
The provided SQL queries are already written and ready to execute. They retrieve the requested information from the database schema.
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.to_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'PHILADELPHIA' AND flight_1.arrival_time > 2100;
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport airport_1 ON flight_1.from_airport = airport_1.airport_code JOIN airport airport_2 ON flight_1.to_airport = airport_2.airport_code WHERE airport_1.airport_code = 'DAL' AND airport_2.airport_code = 'DAL';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code   AND airport_1.airport_code = 'DFW'   AND ground_service_1.city_code = city_1.city_code   AND city_1.city_name = 'DALLAS';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT state_1.state_code FROM state state_1 WHERE state_1.state_code = 'ASD';
SELECT DISTINCT airport_1.airport_code FROM airport airport_1 WHERE airport_1.airport_code = 'MCO'
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT airline_1.airline_code, airline_1.airline_name, airline_1.note FROM airline airline_1 WHERE airline_1.airline_code IN ('UA', 'HP', 'US');
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name IN ('DALLAS', 'DENVER');
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'DENVER';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 INNER JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name IN ('OAKLAND', 'DENVER', 'PHOENIX', 'SAN FRANCISCO');
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE flight_1.airline_code = 'NW' AND flight_1.departure_time < 1200;
SELECT DISTINCT airline_code FROM airline airline_1 JOIN flight flight_1 ON airline_1.airline_code = flight_1.airline_code JOIN airport airport_1 ON flight_1.to_airport = airport_1.airport_code WHERE airport_1.airport_code = 'MKE';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.ground_fare FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.transport_type = 'LIMOUSINE' AND ground_service_1.city_code = city_1.city_code AND city_1.city_name IN ('BOSTON', 'TORONTO', 'LOS ANGELES');
SELECT DISTINCT flight_1.flight_id FROM flight flight_1 JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'DALLAS';
SELECT DISTINCT restriction_1.restriction_code FROM restriction restriction_1 WHERE restriction_1.restriction_code IN ('AP/80', 'AP/57', 'AP/80');
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
The provided SQL queries are already translated from the given questions. They return the flight IDs that satisfy the specified conditions for each question.
SELECT DISTINCT airport_1.airport_code FROM airport airport_1, airport_service airport_service_1, city city_1 WHERE airport_1.airport_code = airport_service_1.airport_code AND airport_service_1.city_code = city_1.city_code AND city_1.city_name = 'WASHINGTON';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport_service airport_service_1, city city_1 WHERE flight_1.airline_code = 'DL'   AND flight_1.from_airport = airport_service_1.airport_code   AND airport_service_1.city_code = city_1.city_code   AND city_1.city_name = 'DENVER';
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code AND airport_1.airport_code = 'BOS' AND ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'BOSTON';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT ground_service_1.transport_type
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name = 'WASHINGTON';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT restriction_1.restriction_code FROM restriction restriction_1 WHERE restriction_1.restriction_code IN ('AP/80', 'AP/57', 'AP/57', 'AP please');
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.time_elapsed
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT class_of_service_1.booking_class
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airport_service_1.miles_distant FROM airport_service airport_service_1, city city_1 WHERE airport_service_1.airport_code = 'OAK' AND city_1.city_code = city_1.city_code AND city_1.city_name IN ('PITTSBURGH', 'ORLANDO');
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 WHERE airline_1.airline_code = 'DL';
SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1 WHERE flight_1.departure_time = (     SELECT MAX( flight_1.departure_time )     FROM flight flight_1, airport airport_1     WHERE flight_1.to_airport = airport_1.airport_code     AND airport_1.airport_code = 'DAL' );
SELECT DISTINCT flight_1.flight_id FROM flight flight_1, airport airport_1 WHERE flight_1.to_airport = airport_1.airport_code AND airport_1.airport_code = 'MKE';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
The provided SQL queries do not contain any information related to the latest evening flights, so I am unable to extract the requested data from the provided context.
SELECT DISTINCT state_1.state_code FROM state state_1 WHERE state_1.state_code = 'ASD';
The provided SQL queries are already written and ready to execute. They retrieve the requested information from the database.
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT ground_service_1.transport_type
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT state_1.state_code FROM state state_1 WHERE state_1.state_code = 'ASD';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.departure_time, flight_1.arrival_time, fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT aircraft_1.aircraft_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1 WHERE ground_service_1.city_code = city_1.city_code AND city_1.city_name IN ('DALLAS', 'DENVER', 'PHILADELPHIA');
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1 INNER JOIN city city_1 ON ground_service_1.city_code = city_1.city_code WHERE city_1.city_name IN ('BOSTON', 'BALTIMORE', 'WASHINGTON') AND ground_service_1.transport_type = 'RENTAL CAR';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_id
SELECT DISTINCT airport_service_1.miles_distant FROM airport_service airport_service_1, city city_1 WHERE airport_service_1.airport_code = 'OAK' AND city_1.city_code = city_1.city_code AND city_1.city_name = 'DALLAS';
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT food_service_1.meal_code, food_service_1.meal_number, food_service_1.compartment
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT count( DISTINCT flight_1.flight_id )
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 JOIN flight flight_1 ON airline_1.airline_code = flight_1.airline_code JOIN airport_service airport_service_1 ON flight_1.to_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'PITTSBURGH'
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT airline_1.airline_code FROM airline airline_1 JOIN flight flight_1 ON airline_1.airline_code = flight_1.airline_code JOIN airport_service airport_service_1 ON flight_1.from_airport = airport_service_1.airport_code JOIN city city_1 ON airport_service_1.city_code = city_1.city_code WHERE city_1.city_name = 'PITTSBURGH'
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT fare_1.fare_id
SELECT DISTINCT aircraft_1.aircraft_code
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, airport airport_1, city city_1 WHERE ground_service_1.airport_code = airport_1.airport_code   AND airport_1.airport_code = 'BOS'   AND ground_service_1.city_code = city_1.city_code   AND city_1.city_name = 'BOSTON';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT ground_service_1.ground_fare
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.departure_time, flight_1.arrival_time
SELECT DISTINCT fare_id
SELECT DISTINCT ground_service_1.transport_type FROM ground_service ground_service_1, city city_1, airport airport_1 WHERE ground_service_1.city_code = city_1.city_code   AND city_1.city_name = 'ATLANTA'   AND ground_service_1.airport_code = airport_1.airport_code   AND airport_1.airport_code = 'ATL';
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT flight_1.departure_time, flight_1.arrival_time
SELECT DISTINCT flight_1.flight_id
SELECT DISTINCT airline_1.airline_code
SELECT DISTINCT flight_1.flight_id
