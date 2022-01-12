-- PROCEDURE: public.update_state_moves_v2(integer, integer, bytea)

-- DROP PROCEDURE IF EXISTS public.update_state_moves_v2(integer, integer, bytea);

CREATE OR REPLACE PROCEDURE public.update_state_moves_v2(
	IN _desk_id integer,
	IN _state integer,
	IN _new_moves bytea)
LANGUAGE 'plpgsql'
AS $BODY$

declare
	_new_moves_decoded jsonb;
	_current_moves_decoded jsonb;
begin
	SELECT msgpack_decode(_new_moves) INTO _new_moves_decoded;
	SELECT ((get_desk_state_moves_decoded(_desk_id, _state)).moves)
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
					_moves_rs.jsonb_array_elements::jsonb->0 = _new_moves_rs.jsonb_array_elements::jsonb->0
				ORDER BY
					_moves_rs.jsonb_array_elements::jsonb->0
				) _jsonb_build_array_rs
			)
		)
		WHERE "State_Moves".state_id = (SELECT get_state_id(_desk_id, _state));
	COMMIT;
end;
$BODY$;
