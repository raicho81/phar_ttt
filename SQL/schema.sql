--
-- PostgreSQL database dump
--

-- Dumped from database version 14.1 (Debian 14.1-1.pgdg110+1)
-- Dumped by pg_dump version 14.1 (Debian 14.1-1.pgdg110+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: adminpack; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS adminpack WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION adminpack; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION adminpack IS 'administrative functions for PostgreSQL';


--
-- Name: add_state_moves(integer, bigint, bytea); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.add_state_moves(IN _desk_id integer, IN _state bigint, IN _moves_encoded bytea)
    LANGUAGE plpgsql
    AS $$
DECLARE 
	state_insert_id integer;
	state_moves_insert_id integer;
BEGIN
	INSERT INTO "States" (desk_id, state, moves)
	VALUES(_desk_id, _state, _moves_encoded)
	ON CONFLICT (desk_id, state) DO NOTHING
	RETURNING id INTO state_insert_id;

	IF state_insert_id IS NULL THEN
		CALL update_state_moves_v2(_desk_id, _state, _moves_encoded);
	END IF;
END;
$$;


ALTER PROCEDURE public.add_state_moves(IN _desk_id integer, IN _state bigint, IN _moves_encoded bytea) OWNER TO postgres;

--
-- Name: get_desk_state_moves(integer, bigint); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_desk_state_moves(_desk_id integer, _state bigint) RETURNS TABLE(state_insert_id integer, moves bytea)
    LANGUAGE sql STABLE ROWS 1 PARALLEL SAFE
    AS $$
SELECT "States".id, "States".moves FROM "States"
WHERE desk_id=_desk_id
AND state=_state
$$;


ALTER FUNCTION public.get_desk_state_moves(_desk_id integer, _state bigint) OWNER TO postgres;

--
-- Name: get_desk_state_moves_decoded(integer, bigint); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_desk_state_moves_decoded(_desk_id integer, _state bigint) RETURNS TABLE(state_insert_id integer, moves jsonb)
    LANGUAGE sql STABLE ROWS 1 PARALLEL SAFE
    AS $$
SELECT "States".id, msgpack_decode("States".moves)
FROM "States"
WHERE desk_id=_desk_id
AND state=_state;
$$;


ALTER FUNCTION public.get_desk_state_moves_decoded(_desk_id integer, _state bigint) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: States; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."States" (
    id integer NOT NULL,
    desk_id integer NOT NULL,
    state bigint NOT NULL,
    moves bytea NOT NULL
);


ALTER TABLE public."States" OWNER TO postgres;

--
-- Name: get_state_id(integer, bigint); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_state_id(_desk_id integer, _state bigint) RETURNS integer
    LANGUAGE sql STABLE COST 5 PARALLEL SAFE
    RETURN (SELECT "States".id FROM public."States" WHERE (("States".desk_id = get_state_id._desk_id) AND ("States".state = get_state_id._state)));


ALTER FUNCTION public.get_state_id(_desk_id integer, _state bigint) OWNER TO postgres;

--
-- Name: has_state(integer, bigint); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.has_state(_desk_id integer, _state bigint) RETURNS boolean
    LANGUAGE plpgsql STABLE COST 5 PARALLEL SAFE
    AS $$
BEGIN
	IF EXISTS (SELECT "States".id FROM "States" WHERE (("States".desk_id = has_state._desk_id) AND ("States".state = has_state._state))) THEN
		RETURN true;
	ELSE
		RETURN false;
	END IF;

END;
$$;


ALTER FUNCTION public.has_state(_desk_id integer, _state bigint) OWNER TO postgres;

--
-- Name: msgpack_decode(bytea); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.msgpack_decode(_data bytea) RETURNS jsonb
    LANGUAGE plpgsql STABLE PARALLEL SAFE
    AS $$
declare _length integer = octet_length(_data);
declare _cursor integer = 0;
declare _size integer;
declare _wrapper jsonb[];
declare _counter integer[];
declare _key text[];
declare _json jsonb;
declare _binary text;
declare _exponent integer;
declare _mantissa text;
declare _float double precision;
declare _index integer;
begin

	while _cursor < _length loop
		case get_byte(_data, _cursor)
			when 192 then -- null
				_json = 'null'::jsonb;
				_cursor = _cursor + 1;
			
			when 194 then -- false
				_json = to_jsonb(false);
				_cursor = _cursor + 1;
			
			when 195 then -- true
				_json = to_jsonb(true);
				_cursor = _cursor + 1;
			
			when 196 then -- bin 8
				_json = 'null'::jsonb;
				_size = get_byte(_data, _cursor + 1);
				_cursor = _cursor + 2 + _size;
			
			when 197 then -- bin 16
				_json = 'null'::jsonb;
				_size = (get_byte(_data, _cursor + 1) << 8)
					+ get_byte(_data, _cursor + 2);
				_cursor = _cursor + 3 + _size;
			
			when 198 then -- bin 32
				_json = 'null'::jsonb;
				_size = (get_byte(_data, _cursor + 1) << 24)
					+ (get_byte(_data, _cursor + 2) << 16)
					+ (get_byte(_data, _cursor + 3) << 8)
					+ get_byte(_data, _cursor + 4);
				_cursor = _cursor + 5 + _size;
			
			when 199 then -- ext 8
				_json = 'null'::jsonb;
				_size = get_byte(_data, _cursor + 1);
				_cursor = _cursor + 3 + _size;
			
			when 200 then -- ext 16
				_json = 'null'::jsonb;
				_size = (get_byte(_data, _cursor + 1) << 8)
					+ get_byte(_data, _cursor + 2);
				_cursor = _cursor + 4 + _size;
			
			when 201 then -- ext 32
				_json = 'null'::jsonb;
				_size = (get_byte(_data, _cursor + 1) << 24)
					+ (get_byte(_data, _cursor + 2) << 16)
					+ (get_byte(_data, _cursor + 3) << 8)
					+ get_byte(_data, _cursor + 4);
				_cursor = _cursor + 6 + _size;
			
			when 202 then -- float 32
				_binary = get_byte(_data, _cursor + 1)::bit(8)
					|| get_byte(_data, _cursor + 2)::bit(8)
					|| get_byte(_data, _cursor + 3)::bit(8)
					|| get_byte(_data, _cursor + 4)::bit(8);
				_exponent = substring(_binary, 2, 8)::bit(8)::integer;
				_mantissa = substring(_binary, 10, 23);

				if _exponent = 255 then
					-- Infinity, -Infinity, NaN
					_json = 'null'::jsonb;
				else
					_float = 1;
					_index = 1;
					_exponent = _exponent - 127;
				
					while _index < 24 loop
						if substring(_mantissa, _index, 1) = '1' then
							_float = _float + (2 ^ -(_index));
						end if;
						_index = _index + 1;
					end loop;

					_float = _float * (2 ^ _exponent);
					if substring(_binary, 1, 1) = '1' then
						_float = -_float;
					end if;
				end if;
				
				_json = to_jsonb(_float);
				_cursor = _cursor + 5;
			
			when 203 then -- float 64
				_binary = get_byte(_data, _cursor + 1)::bit(8)
					|| get_byte(_data, _cursor + 2)::bit(8)
					|| get_byte(_data, _cursor + 3)::bit(8)
					|| get_byte(_data, _cursor + 4)::bit(8)
					|| get_byte(_data, _cursor + 5)::bit(8)
					|| get_byte(_data, _cursor + 6)::bit(8)
					|| get_byte(_data, _cursor + 7)::bit(8)
					|| get_byte(_data, _cursor + 8)::bit(8);
				_exponent = substring(_binary, 2, 11)::bit(11)::integer;
				_mantissa = substring(_binary, 13, 52);

				if _exponent = 2047 then
					-- Infinity, -Infinity, NaN
					_json = 'null'::jsonb;
				else
					_float = 1;
					_index = 1;
					_exponent = _exponent - 1023;
				
					while _index < 53 loop
						if substring(_mantissa, _index, 1) = '1' then
							_float = _float + (2 ^ -(_index));
						end if;
						_index = _index + 1;
					end loop;

					_float = _float * (2 ^ _exponent);
					if substring(_binary, 1, 1) = '1' then
						_float = -_float;
					end if;
				end if;
				
				_json = to_jsonb(_float);
				_cursor = _cursor + 9;
			
			when 204 then -- uint 8
				_json = to_jsonb(get_byte(_data, _cursor + 1));
				_cursor = _cursor + 2;
			
			when 205 then -- uint 16
				_json = to_jsonb((get_byte(_data, _cursor + 1) << 8)
					+ get_byte(_data, _cursor + 2));
				_cursor = _cursor + 3;
			
			when 206 then -- uint 32
				_json = to_jsonb((get_byte(_data, _cursor + 1) << 24)
					+ (get_byte(_data, _cursor + 2) << 16)
					+ (get_byte(_data, _cursor + 3) << 8)
					+ get_byte(_data, _cursor + 4));
				_cursor = _cursor + 5;
			
			when 207 then -- uint 64
				_json = to_jsonb((get_byte(_data, _cursor + 1)::bigint << 56)
					+ (get_byte(_data, _cursor + 2)::bigint << 48)
					+ (get_byte(_data, _cursor + 3)::bigint << 40)
					+ (get_byte(_data, _cursor + 4)::bigint << 32)
					+ (get_byte(_data, _cursor + 5)::bigint << 24)
					+ (get_byte(_data, _cursor + 6)::bigint << 16)
					+ (get_byte(_data, _cursor + 7)::bigint << 8)
					+ get_byte(_data, _cursor + 8)::bigint);
				_cursor = _cursor + 9;
			
			when 208 then -- int 8
				_json = to_jsonb(-(2 ^ 8 - get_byte(_data, _cursor + 1)));
				_cursor = _cursor + 2;
			
			when 209 then -- int 16
				_json = to_jsonb(-(2 ^ 16 - (get_byte(_data, _cursor + 1) << 8)
					- get_byte(_data, _cursor + 2)));
				_cursor = _cursor + 3;
			
			when 210 then -- int 32
				_json = to_jsonb((get_byte(_data, _cursor + 1) << 24)
					+ (get_byte(_data, _cursor + 2) << 16)
					+ (get_byte(_data, _cursor + 3) << 8)
					+ get_byte(_data, _cursor + 4));
				_cursor = _cursor + 5;
			
			when 211 then -- int 64
				_json = to_jsonb((get_byte(_data, _cursor + 1)::bigint << 56)
					+ (get_byte(_data, _cursor + 2)::bigint << 48)
					+ (get_byte(_data, _cursor + 3)::bigint << 40)
					+ (get_byte(_data, _cursor + 4)::bigint << 32)
					+ (get_byte(_data, _cursor + 5)::bigint << 24)
					+ (get_byte(_data, _cursor + 6)::bigint << 16)
					+ (get_byte(_data, _cursor + 7)::bigint << 8)
					+ get_byte(_data, _cursor + 8)::bigint);
				_cursor = _cursor + 9;
			
			when 212 then -- fixext 1
				_json = 'null'::jsonb;
				_cursor = _cursor + 3;
			
			when 213 then -- fixext 2
				_json = 'null'::jsonb;
				_cursor = _cursor + 4;
			
			when 214 then -- fixext 4
				_json = 'null'::jsonb;
				_cursor = _cursor + 6;
			
			when 215 then -- fixext 8
				_json = 'null'::jsonb;
				_cursor = _cursor + 10;
			
			when 216 then -- fixext 16
				_json = 'null'::jsonb;
				_cursor = _cursor + 18;
			
			when 217 then -- str 8
				_size = get_byte(_data, _cursor + 1);
				_json = to_jsonb(convert_from(substring(_data, _cursor + 3, _size), 'utf8'));
				_cursor = _cursor + 2 + _size;
			
			when 218 then -- str 16
				_size = (get_byte(_data, _cursor + 1) << 8)
					+ get_byte(_data, _cursor + 2);
				_json = to_jsonb(convert_from(substring(_data, _cursor + 4, _size), 'utf8'));
				_cursor = _cursor + 3 + _size;
			
			when 219 then -- str 32
				_size = (get_byte(_data, _cursor + 1) << 24)
					+ (get_byte(_data, _cursor + 2) << 16)
					+ (get_byte(_data, _cursor + 3) << 8)
					+ get_byte(_data, _cursor + 4);
				_json = to_jsonb(convert_from(substring(_data, _cursor + 6, _size), 'utf8'));
				_cursor = _cursor + 5 + _size;
			
			when 220 then -- array 16
				_size = (get_byte(_data, _cursor + 1) << 8)
					+ get_byte(_data, _cursor + 2);
				_json = jsonb_build_array();
				_cursor = _cursor + 3;
				if _size > 0 then
					_wrapper = array_prepend(_json, _wrapper);
					_counter = array_prepend(_size, _counter);
					_key = array_prepend(null, _key);
					continue;
				end if;
			
			when 221 then -- array 32
				_size = (get_byte(_data, _cursor + 1) << 24)
					+ (get_byte(_data, _cursor + 2) << 16)
					+ (get_byte(_data, _cursor + 3) << 8)
					+ get_byte(_data, _cursor + 4);
				_json = jsonb_build_array();
				_cursor = _cursor + 5;
				if _size > 0 then
					_wrapper = array_prepend(_json, _wrapper);
					_counter = array_prepend(_size, _counter);
					_key = array_prepend(null, _key);
					continue;
				end if;
			
			when 222 then -- map 16
				_size = (get_byte(_data, _cursor + 1) << 8)
					+ get_byte(_data, _cursor + 2);
				_json = jsonb_build_object();
				_cursor = _cursor + 3;
				if _size > 0 then
					_wrapper = array_prepend(_json, _wrapper);
					_counter = array_prepend(_size, _counter);
					_key = array_prepend(null, _key);
					continue;
				end if;
			
			when 223 then -- map 32
				_size = (get_byte(_data, _cursor + 1) << 24)
					+ (get_byte(_data, _cursor + 2) << 16)
					+ (get_byte(_data, _cursor + 3) << 8)
					+ get_byte(_data, _cursor + 4);
				_json = jsonb_build_object();
				_cursor = _cursor + 5;
				if _size > 0 then
					_wrapper = array_prepend(_json, _wrapper);
					_counter = array_prepend(_size, _counter);
					_key = array_prepend(null, _key);
					continue;
				end if;
	
			else
				if get_byte(_data, _cursor) & 128 = 0 then -- positive fixint
					_json = to_jsonb(get_byte(_data, _cursor));
					_cursor = _cursor + 1;
				elsif get_byte(_data, _cursor) & 224 = 224 then -- negative fixint
					_json = to_jsonb(-(255 - get_byte(_data, _cursor) + 1));
					_cursor = _cursor + 1;
				elsif get_byte(_data, _cursor) & 224 = 160 then -- fixstr
					_size = get_byte(_data, _cursor) & 31;
					_json = to_jsonb(convert_from(substring(_data, _cursor + 2, _size), 'utf8'));
					_cursor = _cursor + 1 + _size;
				elsif get_byte(_data, _cursor) & 240 = 144 then -- fixarray
					_size = get_byte(_data, _cursor) & 15;
					_json = jsonb_build_array();
					_cursor = _cursor + 1;
					if _size > 0 then
						_wrapper = array_prepend(_json, _wrapper);
						_counter = array_prepend(_size, _counter);
						_key = array_prepend(null, _key);
						continue;
					end if;
				elsif get_byte(_data, _cursor) & 240 = 128 then -- fixmap
					_size = get_byte(_data, _cursor) & 15;
					_json = jsonb_build_object();
					_cursor = _cursor + 1;
					if _size > 0 then
						_wrapper = array_prepend(_json, _wrapper);
						_counter = array_prepend(_size, _counter);
						_key = array_prepend(null, _key);
						continue;
					end if;
				else
					raise exception 'Unknown type %.', get_byte(_data, _cursor);
				end if;
		end case;
		
		if _wrapper is null then
			return _json;
		elsif jsonb_typeof(_wrapper[1]) = 'array' then
			_wrapper[1] = _wrapper[1] || jsonb_build_array(_json);
		elsif jsonb_typeof(_wrapper[1]) = 'object' then
			if _key[1] is null then
				_key[1] = _json#>>'{}';
				continue;
			end if;
			_wrapper[1] = _wrapper[1] || jsonb_build_object(_key[1], _json);
			_key[1] = null;
		end if;

		_counter[1] = _counter[1] - 1;
		while _counter[1] <= 0 loop
			_json = _wrapper[1];
			
			_wrapper = _wrapper[2:array_upper(_wrapper, 1)];
			_counter = _counter[2:array_upper(_counter, 1)];
			_key = _key[2:array_upper(_key, 1)];

			if array_length(_wrapper, 1) is null then
				return _json;
			elsif jsonb_typeof(_wrapper[1]) = 'array' then
				_wrapper[1] = _wrapper[1] || jsonb_build_array(_json);
			elsif jsonb_typeof(_wrapper[1]) = 'object' then
				_wrapper[1] = _wrapper[1] || jsonb_build_object(_key[1], _json);
				_key[1] = null;
			end if;
			
			_counter[1] = _counter[1] - 1;
		end loop;
	end loop;

end;
$$;


ALTER FUNCTION public.msgpack_decode(_data bytea) OWNER TO postgres;

--
-- Name: msgpack_encode(jsonb); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.msgpack_encode(_data jsonb) RETURNS bytea
    LANGUAGE plpgsql STABLE PARALLEL SAFE
    AS $$
declare _size integer;
declare _key text;
declare _pack bytea;
declare _chunk bytea;
declare _numeric numeric;
declare _item jsonb;
begin

	case jsonb_typeof(_data)
		when 'object' then
			-- Get count of items in object
			select count(jsonb_object_keys) into _size from jsonb_object_keys(_data);

			if _size < 16 then
				_pack = set_byte(E' '::bytea, 0, (128::bit(8) | _size::bit(8))::integer);
			elsif _size < 2 ^ 16 then
				_pack = E'\\336'::bytea
					|| set_byte(E' '::bytea, 0, _size >> 8)
					|| set_byte(E' '::bytea, 0, _size);
			elsif _size < 2 ^ 32 then
				_pack = E'\\337'::bytea
					|| set_byte(E' '::bytea, 0, _size >> 24)
					|| set_byte(E' '::bytea, 0, _size >> 16)
					|| set_byte(E' '::bytea, 0, _size >> 8)
					|| set_byte(E' '::bytea, 0, _size);
			else
				raise exception 'Maximum number of keys exceeded.';
			end if;
		
			-- Process items
			for _key in select jsonb_object_keys from jsonb_object_keys(_data) loop
				_pack = _pack || public.msgpack_encode(to_jsonb(_key)) || public.msgpack_encode(_data->_key);
			end loop;
		
		when 'array' then
			select jsonb_array_length into _size from jsonb_array_length(_data);

			if _size < 16 then
				_pack = set_byte(E' '::bytea, 0, (144::bit(8) | _size::bit(8))::integer);
			elsif _size < 2 ^ 16 then
				_pack = E'\\334'::bytea
					|| set_byte(E' '::bytea, 0, _size >> 8)
					|| set_byte(E' '::bytea, 0, _size);
			elsif _size < 2 ^ 32 then
				_pack = E'\\335'::bytea
					|| set_byte(E' '::bytea, 0, _size >> 24)
					|| set_byte(E' '::bytea, 0, _size >> 16)
					|| set_byte(E' '::bytea, 0, _size >> 8)
					|| set_byte(E' '::bytea, 0, _size);
			else
				raise exception 'Maximum number of items exceeded.';
			end if;
		
			-- Process items
			for _item in select value from jsonb_array_elements(_data) loop
				_pack = _pack || public.msgpack_encode(_item);
			end loop;
		
		when 'number' then
			_numeric = (_data#>>'{}')::numeric;
			if _numeric % 1 != 0 then
				raise exception 'Float not implemented yet.';
			end if;

			if _numeric > 0 then
				-- Integer
				if _numeric < 2 ^ 7 then
					_pack = set_byte(E' '::bytea, 0, _numeric::integer);
				elsif _numeric < 2 ^ 8 then
					_pack = E'\\314'::bytea
						|| set_byte(E' '::bytea, 0, _numeric::integer);
				elsif _numeric < 2 ^ 16 then
					_pack = E'\\315'::bytea
						|| set_byte(E' '::bytea, 0, (_numeric::integer >> 8) & 255)
						|| set_byte(E' '::bytea, 0, _numeric::integer & 255);
				elsif _numeric < 2 ^ 32 then
					_pack = E'\\316'::bytea
						|| set_byte(E' '::bytea, 0, (_numeric::integer >> 24) & 255)
						|| set_byte(E' '::bytea, 0, (_numeric::integer >> 16) & 255)
						|| set_byte(E' '::bytea, 0, (_numeric::integer >> 8) & 255)
						|| set_byte(E' '::bytea, 0, _numeric::integer & 255);
				elsif _numeric < 2 ^ 64 then
					_pack = E'\\317'::bytea
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 56) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 48) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 40) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 32) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 24) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 16) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 8) & 255)::integer)
						|| set_byte(E' '::bytea, 0, (_numeric::bigint & 255)::integer);
				else
					raise exception 'Integer out of range.';
				end if;
			else
				if _numeric >= -2 ^ 5 then
					_pack = set_byte(E' '::bytea, 0, _numeric::integer);
				elsif _numeric >= -2 ^ 7 then
					_pack = E'\\320'::bytea
						|| set_byte(E' '::bytea, 0, _numeric::integer);
				elsif _numeric >= -2 ^ 15 then
					_pack = E'\\321'::bytea
						|| set_byte(E' '::bytea, 0, (_numeric::integer >> 8) & 255)
						|| set_byte(E' '::bytea, 0, _numeric::integer & 255);
				elsif _numeric >= -2 ^ 31 then
					_pack = E'\\322'::bytea
						|| set_byte(E' '::bytea, 0, (_numeric::integer >> 24) & 255)
						|| set_byte(E' '::bytea, 0, (_numeric::integer >> 16) & 255)
						|| set_byte(E' '::bytea, 0, (_numeric::integer >> 8) & 255)
						|| set_byte(E' '::bytea, 0, _numeric::integer & 255);
				elsif _numeric >= -2 ^ 63 then
					_pack = E'\\323'::bytea
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 56) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 48) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 40) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 32) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 24) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 16) & 255)::integer)
						|| set_byte(E' '::bytea, 0, ((_numeric::bigint >> 8) & 255)::integer)
						|| set_byte(E' '::bytea, 0, (_numeric::bigint & 255)::integer);
				else
					raise exception 'Integer out of range.';
				end if;
			end if;
		
		when 'string' then
			_chunk = convert_to(_data#>>'{}', 'utf8');
			_size = octet_length(_chunk);
			
			if _size <= 31 then
				_pack = set_byte(E' '::bytea, 0, ((160)::bit(8) | (_size)::bit(8))::integer);
			elsif _size <= (2 ^ 8) - 1 then
				_pack = E'\\331'::bytea || set_byte(E' '::bytea, 0, _size);
			elsif _size <= (2 ^ 16) - 1 then
				_pack = E'\\332'::bytea
					|| set_byte(E' '::bytea, 0, _size >> 8)
					|| set_byte(E' '::bytea, 0, _size);
			elsif _size <= (2 ^ 32) - 1 then
				_pack = E'\\333'::bytea
					|| set_byte(E' '::bytea, 0, _size >> 24)
					|| set_byte(E' '::bytea, 0, _size >> 16)
					|| set_byte(E' '::bytea, 0, _size >> 8)
					|| set_byte(E' '::bytea, 0, _size);
			else
				raise exception 'String is too long.';
			end if;
			
			_pack = _pack || _chunk;
	
		when 'boolean' then
			_pack = case _data::text when 'false' then E'\\302'::bytea else E'\\303'::bytea end;

		when 'null' then
			_pack = E'\\300'::bytea;
		
		else
			raise exception '% not implemented yet', jsonb_typeof(_data);
	end case;

	return _pack;

end;
$$;


ALTER FUNCTION public.msgpack_encode(_data jsonb) OWNER TO postgres;

--
-- Name: update_state_moves(integer, bigint, bytea); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.update_state_moves(IN _desk_id integer, IN _state bigint, IN _moves bytea)
    LANGUAGE sql
    AS $$UPDATE "States" SET 
    moves = _moves
WHERE desk_id = _desk_id
AND state = _state$$;


ALTER PROCEDURE public.update_state_moves(IN _desk_id integer, IN _state bigint, IN _moves bytea) OWNER TO postgres;

--
-- Name: update_state_moves_v2(integer, bigint, bytea); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.update_state_moves_v2(IN _desk_id integer, IN _state bigint, IN _new_moves bytea)
    LANGUAGE plpgsql
    AS $$

declare
	_new_moves_decoded jsonb;
	_current_moves_decoded jsonb;
begin
	SELECT msgpack_decode(_new_moves) INTO _new_moves_decoded;
	SELECT ((get_desk_state_moves_decoded(_desk_id, _state)).moves)
			INTO _current_moves_decoded;
	UPDATE "States" SET moves = 
		msgpack_encode(
			(SELECT jsonb_agg(jsonb_build_array) FROM 
				(SELECT jsonb_build_array(
						(_moves_rs.jsonb_array_elements::jsonb->0)::integer,
						(_moves_rs.jsonb_array_elements::jsonb->1)::integer + (_new_moves_rs.jsonb_array_elements::jsonb->1)::integer,
						(_moves_rs.jsonb_array_elements::jsonb->2)::integer + (_new_moves_rs.jsonb_array_elements::jsonb->2)::integer,
						(_moves_rs.jsonb_array_elements::jsonb->3)::integer + (_new_moves_rs.jsonb_array_elements::jsonb->3)::integer
					)
				FROM
					(SELECT jsonb_array_elements(_current_moves_decoded)) _moves_rs,
					(SELECT jsonb_array_elements(_new_moves_decoded)) _new_moves_rs
					WHERE
						_moves_rs.jsonb_array_elements::jsonb->0 = _new_moves_rs.jsonb_array_elements::jsonb->0
					ORDER BY
					_moves_rs.jsonb_array_elements::jsonb->0
				) _jsonb_build_array_rs
			)
		)
		WHERE "States".desk_id = _desk_id and "States".state = _state;
--	COMMIT;
end; 
$$;


ALTER PROCEDURE public.update_state_moves_v2(IN _desk_id integer, IN _state bigint, IN _new_moves bytea) OWNER TO postgres;

--
-- Name: Desks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."Desks" (
    id integer NOT NULL,
    size integer NOT NULL,
    total_games_played integer DEFAULT 0 NOT NULL
);


ALTER TABLE public."Desks" OWNER TO postgres;

--
-- Name: Desks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Desks_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Desks_id_seq" OWNER TO postgres;

--
-- Name: Desks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Desks_id_seq" OWNED BY public."Desks".id;


--
-- Name: States_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."States_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."States_id_seq" OWNER TO postgres;

--
-- Name: States_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."States_id_seq" OWNED BY public."States".id;


--
-- Name: Desks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Desks" ALTER COLUMN id SET DEFAULT nextval('public."Desks_id_seq"'::regclass);


--
-- Name: States id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."States" ALTER COLUMN id SET DEFAULT nextval('public."States_id_seq"'::regclass);


--
-- Name: Desks Desks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Desks"
    ADD CONSTRAINT "Desks_pkey" PRIMARY KEY (id);


--
-- Name: States States_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."States"
    ADD CONSTRAINT "States_pkey" PRIMARY KEY (id);


--
-- Name: Desks size_unique_constraint; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."Desks"
    ADD CONSTRAINT size_unique_constraint UNIQUE (size);


--
-- Name: States_desk_id_state_unique_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX "States_desk_id_state_unique_idx" ON public."States" USING btree (desk_id, state);


--
-- Name: States States_desk_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."States"
    ADD CONSTRAINT "States_desk_id_fkey" FOREIGN KEY (desk_id) REFERENCES public."Desks"(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

