-- PROCEDURE: public.update_state_moves_v2(integer, bytea)

-- DROP PROCEDURE IF EXISTS public.update_state_moves_v2(integer, bytea);

CREATE OR REPLACE PROCEDURE public.update_state_moves_v2(
	IN _state_id integer,
	IN _new_moves bytea)
LANGUAGE 'plpgsql'
    SET jit='true'
AS $BODY$
declare
	_new_moves_decoded jsonb;
	_current_moves_decoded jsonb;
begin
	SELECT msgpack_decode(_new_moves) INTO _new_moves_decoded;
	SELECT msgpack_decode(
			(
				SELECT "State_Moves".moves
				FROM "State_Moves"
				WHERE "State_Moves".state_id = _state_id)
			)
	INTO _current_moves_decoded;
	UPDATE "State_Moves" SET moves =
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
					(_moves_rs.jsonb_array_elements::jsonb->0)::integer = (_new_moves_rs.jsonb_array_elements::jsonb->0)::integer
				ORDER BY
					(_moves_rs.jsonb_array_elements::jsonb->0)::integer
				) _jsonb_build_array_rs
			)
		)
		WHERE state_id = _state_id;
	COMMIT;
end;
$BODY$;
