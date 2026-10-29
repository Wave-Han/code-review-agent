"""
Test suite v2 - 30 Java cases with deliberate FP/FN pressure design.

Distribution:
  - 20 defective cases  -> recall pressure (5 secrets, 6 sqli, 5 empty-catch, 4 debug)
  -  6 clean cases      -> precision pressure (correct counterparts)
  -  4 trap cases       -> precision pressure (look defective, are legal)

Trap cases are intentional: the wide regex rules WILL fire on them,
so the baseline Precision lands below 100% and leaves room for the
Day 9 improvement experiment (context-aware rules).
"""

TEST_CASES_V2 = [
    # ---------- hardcoded_secret (5) ----------
    {
        "id": "J01_secret_field",
        "description": "hardcoded api key in field",
        "code": (
            "public class PaymentClient {\n"
            "    private String API_KEY = \"sk-live-9f8e7d6c5b4a\";\n"
            "    public void pay() { gateway.charge(API_KEY); }\n"
            "}\n"
        ),
        "ground_truth": [("hardcoded_secret", "CRITICAL")],
    },
    {
        "id": "J02_secret_static",
        "description": "hardcoded password constant",
        "code": (
            "public class DbConfig {\n"
            "    static final String PASSWORD = \"admin123\";\n"
            "    static final String USER = \"root\";\n"
            "    public static Connection connect() throws SQLException {\n"
            "        return DriverManager.getConnection(URL, USER, PASSWORD);\n"
            "    }\n"
            "}\n"
        ),
        "ground_truth": [("hardcoded_secret", "CRITICAL")],
    },
    {
        "id": "J03_secret_inline",
        "description": "secret inlined in method body",
        "code": (
            "public String fetchToken() {\n"
            "    String secret = \"AKIAIOSFODNN7EXAMPLE\";\n"
            "    return signer.sign(secret, payload);\n"
            "}\n"
        ),
        "ground_truth": [("hardcoded_secret", "CRITICAL")],
    },
    {
        "id": "J04_secret_token",
        "description": "bearer token hardcoded",
        "code": (
            "public ResponseEntity<String> callApi() {\n"
            "    HttpHeaders headers = new HttpHeaders();\n"
            "    String token = \"Bearer eyJhbGciOiJIUzI1NiJ9.demo.sig\";\n"
            "    headers.add(\"Authorization\", token);\n"
            "    return rest.exchange(url, GET, new HttpEntity<>(headers), String.class);\n"
            "}\n"
        ),
        "ground_truth": [("hardcoded_secret", "CRITICAL")],
    },
    {
        "id": "J05_secret_plus_sqli",
        "description": "multi: secret + sqli in login flow",
        "code": (
            "public boolean login(String u) {\n"
            "    String PASSWORD = \"p@ssw0rd!\";\n"
            "    String sql = \"SELECT * FROM users WHERE name='\" + u + \"' AND pw='\" + PASSWORD + \"'\";\n"
            "    return jdbc.queryForObject(sql, Boolean.class);\n"
            "}\n"
        ),
        "ground_truth": [("hardcoded_secret", "CRITICAL"), ("sql_injection", "CRITICAL")],
    },

    # ---------- sql_injection (6) ----------
    {
        "id": "J06_sqli_concat",
        "description": "classic string concat in WHERE",
        "code": (
            "public User findUser(String name) {\n"
            "    String sql = \"SELECT * FROM users WHERE name='\" + name + \"'\";\n"
            "    return jdbc.queryForObject(sql, userRowMapper);\n"
            "}\n"
        ),
        "ground_truth": [("sql_injection", "CRITICAL")],
    },
    {
        "id": "J07_sqli_builder",
        "description": "StringBuilder assembled query",
        "code": (
            "public List<Order> search(String keyword) {\n"
            "    StringBuilder sql = new StringBuilder(\"SELECT * FROM orders WHERE title LIKE '%\");\n"
            "    sql.append(keyword).append(\"%'\");\n"
            "    return jdbc.query(sql.toString(), orderRowMapper);\n"
            "}\n"
        ),
        "ground_truth": [("sql_injection", "CRITICAL")],
    },
    {
        "id": "J08_sqli_delete",
        "description": "concatenated DELETE",
        "code": (
            "public void remove(String id) {\n"
            "    String sql = \"DELETE FROM cart WHERE id=\" + id;\n"
            "    jdbc.update(sql);\n"
            "}\n"
        ),
        "ground_truth": [("sql_injection", "CRITICAL")],
    },
    {
        "id": "J09_sqli_insert",
        "description": "concatenated INSERT values",
        "code": (
            "public void save(String name, String email) {\n"
            "    String sql = \"INSERT INTO leads(name,email) VALUES('\" + name + \"','\" + email + \"')\";\n"
            "    jdbc.update(sql);\n"
            "}\n"
        ),
        "ground_truth": [("sql_injection", "CRITICAL")],
    },
    {
        "id": "J10_sqli_orderby",
        "description": "dynamic ORDER BY column",
        "code": (
            "public List<Item> list(String sortCol) {\n"
            "    String sql = \"SELECT * FROM items ORDER BY \" + sortCol;\n"
            "    return jdbc.query(sql, itemRowMapper);\n"
            "}\n"
        ),
        "ground_truth": [("sql_injection", "CRITICAL")],
    },
    {
        "id": "J11_sqli_format",
        "description": "String.format into SQL",
        "code": (
            "public User byEmail(String email) {\n"
            "    String sql = String.format(\"SELECT * FROM users WHERE email='%s'\", email);\n"
            "    return jdbc.queryForObject(sql, userRowMapper);\n"
            "}\n"
        ),
        "ground_truth": [("sql_injection", "CRITICAL")],
    },

    # ---------- empty_except (5) ----------
    {
        "id": "J12_empty_catch_bare",
        "description": "empty catch block",
        "code": (
            "public int parse(String s) {\n"
            "    try {\n"
            "        return Integer.parseInt(s);\n"
            "    } catch (NumberFormatException e) {\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        "ground_truth": [("empty_except", "MEDIUM")],
    },
    {
        "id": "J13_empty_catch_comment",
        "description": "catch with only a comment",
        "code": (
            "public void close(Connection c) {\n"
            "    try {\n"
            "        c.close();\n"
            "    } catch (SQLException e) {\n"
            "        // ignore on close\n"
            "    }\n"
            "}\n"
        ),
        "ground_truth": [("empty_except", "MEDIUM")],
    },
    {
        "id": "J14_empty_catch_return",
        "description": "catch swallows and returns default silently",
        "code": (
            "public double ratio(double a, double b) {\n"
            "    try {\n"
            "        return a / b;\n"
            "    } catch (ArithmeticException e) {\n"
            "        return 0;\n"
            "    }\n"
    "}\n"
        ),
        "ground_truth": [("empty_except", "MEDIUM")],
    },
    {
        "id": "J15_empty_catch_multiline",
        "description": "swallow IO error in reader loop",
        "code": (
            "public String readAll(Path p) {\n"
            "    StringBuilder sb = new StringBuilder();\n"
            "    try (BufferedReader r = Files.newBufferedReader(p)) {\n"
            "        String line;\n"
            "        while ((line = r.readLine()) != null) { sb.append(line); }\n"
            "    } catch (IOException e) {\n"
            "    }\n"
            "    return sb.toString();\n"
            "}\n"
        ),
        "ground_truth": [("empty_except", "MEDIUM")],
    },
    {
        "id": "J16_sqli_plus_emptycatch",
        "description": "multi: sqli attempt wrapped in empty catch",
        "code": (
            "public String find(String name) {\n"
            "    try {\n"
            "        String sql = \"SELECT * FROM t WHERE n='\" + name + \"'\";\n"
            "        return jdbc.queryForObject(sql, String.class);\n"
            "    } catch (DataAccessException e) {\n"
            "    }\n"
            "    return null;\n"
            "}\n"
        ),
        "ground_truth": [("sql_injection", "CRITICAL"), ("empty_except", "MEDIUM")],
    },

    # ---------- debug_print (4) ----------
    {
        "id": "J17_debug_println",
        "description": "println with debug marker in business logic",
        "code": (
            "public Order checkout(Cart cart) {\n"
            "    System.out.println(\"debug: cart=\" + cart);\n"
            "    Order order = orderService.create(cart);\n"
            "    System.out.println(\"debug: order=\" + order.getId());\n"
            "    return order;\n"
            "}\n"
        ),
        "ground_truth": [("debug_print", "LOW")],
    },
    {
        "id": "J18_debug_stacktrace",
        "description": "printStackTrace left in production path",
        "code": (
            "public void sync() {\n"
            "    try {\n"
            "        client.push(data);\n"
            "    } catch (RpcException e) {\n"
            "        e.printStackTrace();\n"
            "    }\n"
            "}\n"
        ),
        "ground_truth": [("debug_print", "LOW")],
    },
    {
        "id": "J19_debug_printf_style",
        "description": "System.out.printf debugging values",
        "code": (
            "public double applyDiscount(double price, User u) {\n"
            "    System.out.printf(\"debug price=%s user=%s%n\", price, u.getId());\n"
            "    return price * (1 - u.tier());\n"
            "}\n"
        ),
        "ground_truth": [("debug_print", "LOW")],
    },
    {
        "id": "J20_debug_secret_leak",
        "description": "multi: println leaking credentials",
        "code": (
            "public void connect() {\n"
            "    String PASSWORD = \"hunter2\";\n"
            "    System.out.println(\"debug connecting with \" + PASSWORD);\n"
            "    pool.open(PASSWORD);\n"
            "}\n"
        ),
        "ground_truth": [("hardcoded_secret", "CRITICAL"), ("debug_print", "LOW")],
    },

    # ---------- clean counterparts (6) ----------
    {
        "id": "C01_clean_secret_env",
        "description": "secret from environment variable",
        "code": (
            "public class PaymentClient {\n"
            "    private final String apiKey = System.getenv(\"PAYMENT_API_KEY\");\n"
            "    public void pay() { gateway.charge(apiKey); }\n"
            "}\n"
        ),
        "ground_truth": [],
    },
    {
        "id": "C02_clean_sqli_prepared",
        "description": "parameterized query with placeholders",
        "code": (
            "public User findUser(String name) {\n"
            "    return jdbc.queryForObject(\n"
            "        \"SELECT * FROM users WHERE name = ?\",\n"
            "        userRowMapper, name);\n"
            "}\n"
        ),
        "ground_truth": [],
    },
    {
        "id": "C03_clean_catch_log_rethrow",
        "description": "catch logs and rethrows properly",
        "code": (
            "public void sync() {\n"
            "    try {\n"
            "        client.push(data);\n"
            "    } catch (RpcException e) {\n"
            "        log.error(\"push failed for batch {}\", batchId, e);\n"
            "        throw new SyncException(e);\n"
            "    }\n"
            "}\n"
        ),
        "ground_truth": [],
    },
    {
        "id": "C04_clean_logger",
        "description": "proper logger instead of println",
        "code": (
            "public Order checkout(Cart cart) {\n"
            "    log.debug(\"cart={} itemCount={}\", cart.getId(), cart.size());\n"
            "    return orderService.create(cart);\n"
            "}\n"
        ),
        "ground_truth": [],
    },
    {
        "id": "C05_clean_static_sql",
        "description": "static SQL constant without concatenation",
        "code": (
            "public class Queries {\n"
            "    private static final String FIND_ALL = \"SELECT id, name FROM items\";\n"
            "    public List<Item> all() { return jdbc.query(FIND_ALL, itemRowMapper); }\n"
            "}\n"
        ),
        "ground_truth": [],
    },
    {
        "id": "C06_clean_validation",
        "description": "input validation and safe defaults",
        "code": (
            "public int parsePort(String s, int def) {\n"
            "    try {\n"
            "        int p = Integer.parseInt(s);\n"
            "        return (p > 0 && p < 65536) ? p : def;\n"
            "    } catch (NumberFormatException e) {\n"
            "        log.warn(\"invalid port '{}', using default\", s);\n"
            "        return def;\n"
            "    }\n"
            "}\n"
        ),
        "ground_truth": [],
    },

    # ---------- trap cases (4): look defective, are legal ----------
    {
        "id": "T01_trap_test_constant",
        "description": "test fixture constant looks like a leaked secret",
        "code": (
            "class PaymentClientTest {\n"
            "    private static final String TEST_API_KEY = \"test-key-not-real\";\n"
            "    void chargeDeclinedCard() {\n"
            "        mockGateway.expectKey(TEST_API_KEY);\n"
            "    }\n"
            "}\n"
        ),
        "ground_truth": [],
    },
    {
        "id": "T02_trap_main_println",
        "description": "println in main is program output, not debug",
        "code": (
            "public class CliMain {\n"
            "    public static void main(String[] args) {\n"
            "        Result r = runner.run(args);\n"
            "        System.out.println(\"Result: \" + r.summary());\n"
            "    }\n"
            "}\n"
        ),
        "ground_truth": [],
    },
    {
        "id": "T03_trap_sql_in_string_literal",
        "description": "SQL keywords inside a plain string, no query built",
        "code": (
            "public class Docs {\n"
            "    public String warning() {\n"
            "        return \"Never do: SELECT * FROM users WHERE name='\" + user + \"'\";\n"
            "    }\n"
            "}\n"
        ),
        "ground_truth": [],
    },
    {
        "id": "T04_trap_debug_logger_name",
        "description": "logger named debug, unrelated to print",
        "code": (
            "public class Telemetry {\n"
            "    private final Logger debug = Logger.getLogger(\"telemetry\");\n"
            "    public void report() { debug.info(() -> \"beat \" + counter); }\n"
            "}\n"
        ),
        "ground_truth": [],
    },
]
