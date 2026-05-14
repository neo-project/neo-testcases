
from neo import *
from neo.contract import *
from testcases.testing import Testing


# Operation: verify OpCode.EQUAL semantics (neo-vm types: Null, Bool, Int, Buffer,
# ByteString, Array, Map, Struct).
#
# 1. for primitive types: Null, Bool, Int, ByteString, the equal is value equal.
# 2. for compound types: Array, Map, Buffer, the equal is reference equal.
# 3. any non-Null item compared with Null via EQUAL yields false (never equal).
class OpEqual(Testing):
    def __init__(self):
        super().__init__("OpEqual")

    def _expect_halt_boolean(self, result: dict, expected: bool, label: str):
        self.logger.info(f"{label} invoke result: {result}")
        assert result.get('exception') is None, result.get('exception')
        self.check_stack(result['stack'], [('Boolean', expected)])

    def _expect_fault(self, result: dict, label: str):
        self.logger.info(f"{label} invoke result: {result}")
        assert 'exception' in result and result['exception'] is not None, result

    def _null_equal(self):
        script = ScriptBuilder() \
            .emit(OpCode.PUSHNULL) \
            .emit(OpCode.PUSHNULL) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, True, "null == null")

    def _non_null_vs_null(self):
        """Each VM type other than Null compared with Null: EQUAL must push false (HALT)."""
        def run(script: bytes, label: str):
            result = self.client.invoke_script(script)
            self._expect_halt_boolean(result, False, label)

        script = ScriptBuilder().emit(OpCode.PUSHT).emit(OpCode.PUSHNULL).emit(OpCode.EQUAL).to_bytes()
        run(script, "bool true vs null")

        script = ScriptBuilder().emit(OpCode.PUSHF).emit(OpCode.PUSHNULL).emit(OpCode.EQUAL).to_bytes()
        run(script, "bool false vs null")

        script = ScriptBuilder().emit_push_int(0).emit(OpCode.PUSHNULL).emit(OpCode.EQUAL).to_bytes()
        run(script, "int vs null")

        script = ScriptBuilder().emit_push_int(42).emit(OpCode.PUSHNULL).emit(OpCode.EQUAL).to_bytes()
        run(script, "int 42 vs null")

        script = ScriptBuilder().emit_push_bytes(b"").emit(OpCode.PUSHNULL).emit(OpCode.EQUAL).to_bytes()
        run(script, "empty ByteString vs null")

        script = ScriptBuilder().emit_push_bytes(b"neo").emit(OpCode.PUSHNULL).emit(OpCode.EQUAL).to_bytes()
        run(script, "ByteString vs null")

        script = ScriptBuilder().emit(OpCode.NEWARRAY0).emit(OpCode.PUSHNULL).emit(OpCode.EQUAL).to_bytes()
        run(script, "empty Array vs null")

        script = ScriptBuilder().emit(OpCode.NEWMAP).emit(OpCode.PUSHNULL).emit(OpCode.EQUAL).to_bytes()
        run(script, "Map vs null")

        script = ScriptBuilder().emit_push_int(1).emit(OpCode.NEWBUFFER).emit(OpCode.PUSHNULL).emit(OpCode.EQUAL).to_bytes()
        run(script, "Buffer vs null")

        script = ScriptBuilder().emit(OpCode.PUSHNULL).emit(OpCode.PUSHT).emit(OpCode.EQUAL).to_bytes()
        run(script, "null vs bool true")

        # Operand order reversed: null under non-null on stack — still not equal.
        script = ScriptBuilder().emit(OpCode.PUSHNULL).emit(OpCode.PUSHF).emit(OpCode.EQUAL).to_bytes()
        run(script, "null vs bool false")

    def _bool_equal(self):
        # PUSHT / PUSHF push Bool stack items (PUSH0 / PUSH1 are Integer).
        script = ScriptBuilder() \
            .emit(OpCode.PUSHT) \
            .emit(OpCode.PUSHT) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, True, "bool true == true")

        script = ScriptBuilder() \
            .emit(OpCode.PUSHF) \
            .emit(OpCode.PUSHF) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, True, "bool false == false")

        script = ScriptBuilder() \
            .emit(OpCode.PUSHF) \
            .emit(OpCode.PUSHT) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, False, "bool false == true")

    def _int_equal(self):
        script = ScriptBuilder() \
            .emit_push_int(42) \
            .emit_push_int(42) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, True, "int 42 == 42")

        script = ScriptBuilder() \
            .emit_push_int(1) \
            .emit_push_int(2) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, False, "int 1 == 2")

    def _bytestring_equal(self):
        script = ScriptBuilder() \
            .emit_push_bytes(b"neo") \
            .emit_push_bytes(b"neo") \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, True, "ByteString neo == neo")

        script = ScriptBuilder() \
            .emit_push_bytes(b"a") \
            .emit_push_bytes(b"b") \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, False, "ByteString a == b")

    def _array_equal(self):
        script = ScriptBuilder() \
            .emit(OpCode.NEWARRAY0) \
            .emit(OpCode.NEWARRAY0) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, False, "Different empty arrays are not equal")

        script = ScriptBuilder() \
            .emit(OpCode.NEWARRAY0) \
            .emit(OpCode.DUP) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, True, "Same reference arrays are equal")

    def _map_equal(self):
        script = ScriptBuilder() \
            .emit(OpCode.NEWMAP) \
            .emit(OpCode.NEWMAP) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, False, "Different empty maps are not equal")

        script = ScriptBuilder() \
            .emit(OpCode.NEWMAP) \
            .emit(OpCode.DUP) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, True, "Same reference maps are equal")

    def _buffer_equal(self):
        # NEWBUFFER: top stack item is length; creates VM Buffer (not ByteString).
        script = ScriptBuilder() \
            .emit_push_int(1) \
            .emit(OpCode.NEWBUFFER) \
            .emit_push_int(1) \
            .emit(OpCode.NEWBUFFER) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, False, "Different empty buffers are not equal")

        script = ScriptBuilder() \
            .emit_push_int(1) \
            .emit(OpCode.NEWBUFFER) \
            .emit(OpCode.DUP) \
            .emit(OpCode.EQUAL) \
            .to_bytes()
        result = self.client.invoke_script(script)
        self._expect_halt_boolean(result, True, "Same reference buffers are equal")

    def run_test(self):
        self._null_equal()
        self._non_null_vs_null()
        self._bool_equal()
        self._int_equal()
        self._bytestring_equal()
        self._array_equal()
        self._map_equal()
        self._buffer_equal()


# Run with: python3 -B -m testcases.system.opcode.op_equal
if __name__ == "__main__":
    test = OpEqual()
    test.run()
