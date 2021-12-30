import msgpack


class TTTDataEncoder:
    def __init__(self, *args, **kwargs):
        pass

    def encode(self, data):
        raise NotImplementedError

    def decode(self, data):
        raise NotImplementedError

class TTTDataEncoderNone(TTTDataEncoder):
    def __init__(self, *args, **kwargs):
        pass

    def encode(self, data):
        return data

    def decode(self, data):
        return data

class TTTDataEncoderMsgpack(TTTDataEncoder):
    def __init__(self, *args, **kwargs):
        pass

    # def decode_TTTTrainDataMove(self, obj):
    #     if '__TTTTrainDataMove__' in obj:
    #         fields = obj["fields"]
    #         obj = ttt_train_data.TTTTrainDataMove(fields[0], fields[1], fields[2], fields[3])
    #     return obj

    # def encode_TTTTrainDataMove(self, obj):
    #     if isinstance(obj, ttt_train_data.TTTTrainDataMove):
    #         return {'__TTTTrainDataMove__': True, 'fields': [obj.move_idx, obj.n_wins, obj.n_draws, obj.n_looses]}
    #     return obj

    def encode(self, data):
        # return msgpack.packb(data, default=TTTDataEncoder.encode_TTTTrainDataMove, use_bin_type=True)
        return msgpack.packb(data, use_bin_type=True)

    def decode(self, data):
        # return msgpack.unpackb(data, object_hook=TTTDataEncoder.decode_TTTTrainDataMove, raw=False)
        return msgpack.unpackb(data, raw=False)
