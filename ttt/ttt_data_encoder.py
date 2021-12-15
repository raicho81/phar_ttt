import msgpack

import ttt_train_data


class TTTDataEncoderNone:
    @staticmethod
    def encode(data):
        return data
    
    @staticmethod
    def decode(data):
        return data
    
class TTTDataEncoder:

    @staticmethod
    def decode_TTTTrainDataMove(obj):
        if '__TTTTrainDataMove__' in obj:
            fields = obj["fields"]
            obj = ttt_train_data.TTTTrainDataMove(fields[0], fields[1], fields[2], fields[3])
        return obj

    @staticmethod
    def encode_TTTTrainDataMove(obj):
        if isinstance(obj, ttt_train_data.TTTTrainDataMove):
            return {'__TTTTrainDataMove__': True, 'fields': [obj.move_idx, obj.n_wins, obj.n_draws, obj.n_looses]}
        return obj

    @staticmethod
    def encode(data):
        # return msgpack.packb(data, default=TTTDataEncoder.encode_TTTTrainDataMove, use_bin_type=True)
        return msgpack.packb(data, use_bin_type=True)

    @staticmethod
    def decode(data):
        # return msgpack.unpackb(data, object_hook=TTTDataEncoder.decode_TTTTrainDataMove, raw=False)
        return msgpack.unpackb(data, raw=False)
