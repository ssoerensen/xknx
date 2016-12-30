import unittest

from xknx import KNXIPFrame,Address,DPT_Time,DPT_Binary,DPT_Array,DPT_Temperature,Telegram,TelegramType

class Test_KNXIP(unittest.TestCase):

    def test_from_knx(self):

        raw = ((0x06,0x10,0x05,0x30,0x00,0x12,0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x02,0x00,0x40,0xf0))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        self.assertEqual( knxipframe.sender ,  Address("1.2.2") )
        self.assertEqual(knxipframe.group_address, Address(337))

        self.assertEqual(len(knxipframe.cemi.payload.value),1)
        self.assertEqual(knxipframe.cemi.payload.value[0],0xf0)

    def test_from_knx_to_knx(self):

        raw = ((0x06,0x10,0x05,0x30,0x00,0x12, 0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x02,0x00, 0x40,0xf0))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        knxipframe.normalize()

        self.assertEqual(knxipframe.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe.cemi.to_knx(), list(raw[6:]))
        self.assertEqual( knxipframe.to_knx(), list(raw))

    def test_telegram_set(self):
        knxipframe = KNXIPFrame()
        knxipframe.sender = Address("1.2.2")

        telegram = Telegram()
        telegram.group_address= Address(337)

        telegram.payload = DPT_Array (DPT_Time().to_knx(
                    {'hours': 13, 'minutes': 23, 'seconds': 42}))

        knxipframe.telegram = telegram

        knxipframe.cemi.set_hops(5)
        knxipframe.normalize()

        raw = ((0x06,0x10,0x05,0x30,0x00,0x14,0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x04,0x00,0x80,13,23,42))

        self.assertEqual(knxipframe.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe.cemi.to_knx(), list(raw[6:]))
        self.assertEqual( knxipframe.to_knx(), list(raw))

    def test_telegram_get(self):

        raw = ((0x06,0x10,0x05,0x30,0x00,0x12,0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x02,0x00,0x40,0xf0))
        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        telegram = knxipframe.telegram

        self.assertEqual(telegram.group_address, Address(337))

        self.assertEqual(len(telegram.payload.value),1)
        self.assertEqual(telegram.payload.value[0],0xf0)

    ########################################################
    #
    # NEW TESTS BELOW 
    #
    ########################################################
    
    def test_binary_switch_on(self):
        # Switch on Kitchen-L1
        raw = (( 0x06,0x10,0x05,0x30,0x00,0x11,0x29,0x00,0xbc,0xd0,0xff,0xf9,0x01,0x49,0x01,0x00,0x81 ))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)
        telegram = knxipframe.telegram
        self.assertEqual(telegram, Telegram(Address("329"), payload=DPT_Binary(1) ) )

        knxipframe2 = KNXIPFrame()
        knxipframe2.sender = Address("15.15.249")
        knxipframe2.telegram = telegram
        knxipframe2.cemi.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.cemi.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))


    def test_payload_1byte(self):
        # Dimm Kitchen L1 to 0x65
        raw = (( 0x06,0x10,0x05,0x30,0x00,0x12,0x29,0x00,0xbc,0xd0,0xff,0xf9,0x01,0x4b,0x02,0x00,0x80,0x65 ))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)
        telegram = knxipframe.telegram
        self.assertEqual(telegram, Telegram(Address("331"), payload=DPT_Array(0x65) ) )

        knxipframe2 = KNXIPFrame()
        knxipframe2.sender = Address("15.15.249")
        knxipframe2.telegram = telegram
        knxipframe2.cemi.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.cemi.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_payload_2bytes(self):
        # Incoming Temperature from thermostat
        raw = (( 0x06,0x10,0x05,0x30,0x00,0x13,0x29,0x00,0xbc,0xd0,0x14,0x02,0x08,0x01,0x03,0x00,0x80,0x07,0xc1 ))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)
        telegram = knxipframe.telegram
        self.assertEqual(telegram, Telegram(Address("2049"), payload=DPT_Array(DPT_Temperature().to_knx(19.85) ) ) )

        knxipframe2 = KNXIPFrame()
        knxipframe2.sender = Address("1.4.2")
        knxipframe2.telegram = telegram
        knxipframe2.cemi.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.cemi.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_state_request(self):
        # State request
        raw = (( 0x06,0x10,0x05,0x30,0x00,0x11,0x29,0x00,0xbc,0xd0,0xff,0xf9,0x01,0xb8,0x01,0x00,0x00 ))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)
        telegram = knxipframe.telegram
        print(telegram)
        print(Telegram(Address("440"), TelegramType.GROUP_WRITE ))
        self.assertEqual(telegram, Telegram(Address("440"), TelegramType.GROUP_WRITE ) )

        knxipframe2 = KNXIPFrame()
        knxipframe2.sender = Address("15.15.249")
        knxipframe2.telegram = telegram
        knxipframe2.cemi.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.cemi.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))



    # Incoming state 
    # 06 10 05 30 00 11 29 00 bc d0 13 01 01 88 01 00 41

suite = unittest.TestLoader().loadTestsFromTestCase(Test_KNXIP)
unittest.TextTestRunner(verbosity=2).run(suite)
