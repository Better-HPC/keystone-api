"""Unit tests for the `SecureSandboxedEnvironment` class."""

from datetime import datetime

from django.test import SimpleTestCase

from plugins.email import SecureSandboxedEnvironment


class IsSafeAttributeMethod(SimpleTestCase):
    """Test validation of attributes by the `is_safe_attribute` method."""

    def setUp(self) -> None:
        """Instantiate a new sandboxed environment."""

        self.env = SecureSandboxedEnvironment()

    def test_blocks_private_attributes(self) -> None:
        """Verify attributes starting with an underscore are blocked."""

        result = self.env.is_safe_attribute(object(), '_private', None)
        self.assertFalse(result)

    def test_blocks_forbidden_attributes(self) -> None:
        """Verify explicitly forbidden attributes are blocked."""

        self.assertFalse(self.env.is_safe_attribute(object(), 'objects', None))
        self.assertFalse(self.env.is_safe_attribute(object(), 'password', None))
        self.assertFalse(self.env.is_safe_attribute(object(), 'history', None))

    def test_allows_public_safe_attributes(self) -> None:
        """Verify normal public attributes are allowed."""

        class Dummy:
            public_attr = 123

        dummy = Dummy()
        result = self.env.is_safe_attribute(dummy, 'public_attr', dummy.public_attr)
        self.assertTrue(result)


class IsSafeCallableMethod(SimpleTestCase):
    """Test validation of methods by the `is_safe_callable` method."""

    def setUp(self) -> None:
        """Instantiate a new sandboxed environment."""
        self.env = SecureSandboxedEnvironment()

    def test_allows_builtin_constructors(self) -> None:
        """Verify builtin constructors are allowed."""

        self.assertTrue(self.env.is_safe_callable(str))
        self.assertTrue(self.env.is_safe_callable(bool))
        self.assertTrue(self.env.is_safe_callable(float))

    def test_allows_builtin_functions(self) -> None:
        """Verify builtin methods are allowed."""

        self.assertTrue(self.env.is_safe_callable(len))
        self.assertTrue(self.env.is_safe_callable(max))
        self.assertTrue(self.env.is_safe_callable(min))
        self.assertTrue(self.env.is_safe_callable(sorted))

    def test_allows_primitive_methods(self) -> None:
        """Verify methods from primitive types are allowed."""

        self.assertTrue(self.env.is_safe_callable("example".upper))
        self.assertTrue(self.env.is_safe_callable([].append))
        self.assertTrue(self.env.is_safe_callable({}.get))
        self.assertTrue(self.env.is_safe_callable(datetime.now().isoformat))

    def test_blocks_unbound_functions(self) -> None:
        """Verify unbound functions (e.g., global functions, lambdas) are blocked."""

        def global_func() -> str:
            return "unsafe"

        self.assertFalse(self.env.is_safe_callable(global_func))
        self.assertFalse(self.env.is_safe_callable(lambda x: x * 2))

    def test_blocks_callables_from_custom_classes(self) -> None:
        """Verify methods from non-primitive types are blocked."""

        class Custom:
            def method(self) -> str:
                return "not allowed"

        obj = Custom()
        self.assertFalse(self.env.is_safe_callable(obj.method))

    def test_blocks_primitive_subclasses(self) -> None:
        """Verify subclassed primitive types are not treated as safe."""

        class DangerousStr(str):
            def secret(self) -> str:
                return "exposed"

        self.assertFalse(self.env.is_safe_callable(DangerousStr))
        self.assertFalse(self.env.is_safe_callable(DangerousStr("hello").secret))
