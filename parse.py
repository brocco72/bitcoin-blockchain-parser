import struct
import os
import hashlib
import json
import time
import itertools
from collections import OrderedDict


def uint1(stream):
    return ord(stream.read(1))


def uint2(stream):
    return struct.unpack('H', stream.read(2))[0]


def uint4(stream):
    return struct.unpack('I', stream.read(4))[0]


def uint8(stream):
    return struct.unpack('Q', stream.read(8))[0]


def hash32(stream):
    return stream.read(32)[::-1]


def varint(stream):
    size = uint1(stream)
    if size < 0xfd:
        print '1'
        return struct.pack('B', size).encode('hex')
    if size == 0xfd:
        print '2'
        return struct.pack('H', uint2(stream)).encode('hex')
    if size == 0xfe:
        print '4'
        return struct.pack('I', uint4(stream)).encode('hex')
    if size == 0xff:
        print '8'
        return struct.pack('Q', uint8(stream)).encode('hex')
    return -1


def hashStr(bytebuffer):
    return ''.join(('%0.2X' % ord(a)) for a in bytebuffer)


def changeIndianness(hash):
    hash = hash.decode('hex')
    returnHash = ""
    for byte in reversed(bytearray(hash)):
        returnHash += ('%0.2X' % byte)
    return returnHash


def get_blk():
    list = []
    for file in os.listdir("/home/dude/.bitcoin/blocks"):
        if file.startswith("blk"):
            list.append(file)
    list.sort()
    return list


class Block(object):
    def __init__(self, blockchain):
        self.magicNum = uint4(blockchain)
        self.blocksize = uint4(blockchain)
        self.setHeader(blockchain)
        self.txCount = changeIndianness(varint(blockchain))
        self.Txs = []
        if long(self.txCount,16) < 100000:
            for i in range(0, long(self.txCount,16)):
                tx = Tx(blockchain)
                self.Txs.append(tx)

    def setHeader(self, blockchain):
        self.blockHeader = BlockHeader(blockchain)


class BlockHeader(object):
    def __init__(self, blockchain):
        self.version = uint4(blockchain)
        self.previousHash = hash32(blockchain)
        self.merkleHash = hash32(blockchain)
        self.time = uint4(blockchain)
        self.bits = uint4(blockchain)
        self.nonce = uint4(blockchain)


class Tx(object):
    def __init__(self, blockchain):
        self.hash = ""
        self.version = uint4(blockchain)
        self.inCount = changeIndianness(varint(blockchain))
        self.inputs = []
        for i in range(0, long(self.inCount,16)):
            input = TxInput(blockchain).get_dict()
            self.inputs.append(input)
        self.outCount = changeIndianness(varint(blockchain))
        self.outputs = []
        if self.outCount > 0:
            for i in range(0, long(self.outCount,16)):
                output = TxOutput(blockchain).get_dict()
                self.outputs.append(output)
        self.lockTime = uint4(blockchain)

    def set_hash(self):
        to_hash = struct.pack('I', self.version).encode('hex') + self.inCount
        for input in self.inputs:
            for key, value in input.items():
                to_hash += str(value)
        to_hash += self.outCount
        for output in self.outputs:
            for key, value in output.items():
                to_hash += str(value)
        to_hash += struct.pack('I', self.lockTime).encode('hex')
        self.hash = changeIndianness(hashlib.sha256(hashlib.sha256(to_hash.decode('hex')).digest()).hexdigest())

    def get_dict(self):
        toReturn = OrderedDict()
        toReturn['hash'] = self.hash
        toReturn['version'] = self.version
        toReturn['inCount'] = self.inCount
        toReturn['inputs'] = self.inputs
        toReturn['outCount'] = self.outCount
        toReturn['outputs'] = self.outputs
        toReturn['lockTime'] = self.lockTime
        return toReturn


class TxInput(object):
    def __init__(self, blockchain):
        self.prevTxHash = hash32(blockchain).encode('hex')
        self.index = changeIndianness(struct.pack('I', uint4(blockchain)).encode('hex'))
        self.scriptLen = changeIndianness(varint(blockchain))
        self.scriptSig = hashStr(blockchain.read(long(self.scriptLen, 16)))
        self.seqNo = struct.pack('I', uint4(blockchain)).encode('hex')

    def get_dict(self):
        toReturn = OrderedDict()
        toReturn['prevTxHash'] = changeIndianness(self.prevTxHash).upper()
        toReturn['index'] = changeIndianness(self.index)
        toReturn['scriptLen'] = self.scriptLen.upper()
        toReturn['scriptSig'] = self.scriptSig
        toReturn['seqNo'] = self.seqNo
        return toReturn


class TxOutput(object):
    def __init__(self, blockchain):
        self.value = changeIndianness(struct.pack('Q', uint8(blockchain)).encode('hex'))
        self.scriptLen = varint(blockchain)
        self.script = hashStr(blockchain.read(long(self.scriptLen, 16)))

    def get_dict(self):
        toReturn = OrderedDict()
        toReturn['value'] = changeIndianness(self.value)
        toReturn['scriptLen'] = changeIndianness(self.scriptLen).upper()
        toReturn['script'] = self.script
        return toReturn


def main():
    list = get_blk()
    path = '/home/dude/.bitcoin/blocks/' + list[1]
    # counter = 0
    with open(path, 'rb') as test:
         while True:
            if not test:
                break
            for tx in Block(test).Txs:
                tx.set_hash()
            with open("blk00001.txt", 'a') as writer:
                writer.write(json.dumps(tx.get_dict()))


if __name__ == '__main__':
    main()