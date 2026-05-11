import 'dart:convert';
import 'dart:io';

void main() {
  final file = File('figma/tokens_to_figma.json');
  if (!file.existsSync()) {
    print('Error: figma/tokens_to_figma.json not found');
    return;
  }

  Directory('lib/theme').createSync(recursive: true);

  final data = json.decode(file.readAsStringSync()) as Map<String, dynamic>;
  final colorMap = _buildColorMap(data);

  _generateColors(data, colorMap);
  _generateDimension(data);
  _generateTypography(data);

  print('Design tokens generated successfully in lib/theme/');
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

String _cap(String s) =>
    s.isNotEmpty ? '${s[0].toUpperCase()}${s.substring(1)}' : s;

/// Converts a token key that may start with a digit to a valid Dart identifier.
/// e.g. '2xl' → 'xl2', '3xl' → 'xl3'
String _safeName(String key) {
  final match = RegExp(r'^(\d+)(.*)$').firstMatch(key);
  if (match != null) return '${match.group(2)}${match.group(1)}';
  return key;
}

/// Converts #RRGGBB or #RRGGBBAA → Flutter Color(0xAARRGGBB).
String _hexToColor(String hex) {
  hex = hex.replaceAll('#', '');
  if (hex.length == 8) {
    final aa = hex.substring(6, 8).toUpperCase();
    return 'Color(0x$aa${hex.substring(0, 6).toUpperCase()})';
  }
  return 'Color(0xFF${hex.toUpperCase()})';
}

// ---------------------------------------------------------------------------
// Color reference resolution  (brand → alias → component)
// ---------------------------------------------------------------------------

Map<String, String> _buildColorMap(Map<String, dynamic> data) {
  final brand = data['brand'] as Map<String, dynamic>;
  final alias = data['alias'] as Map<String, dynamic>;

  // Flatten brand: 'pink.500' → '#ec4899', 'core.white' → '#ffffff', 'white' → '#ffffff'
  final primitives = <String, String>{};
  brand.forEach((group, groupData) {
    if (groupData is! Map<String, dynamic>) return;
    groupData.forEach((key, node) {
      if (node is Map<String, dynamic> && node['value'] is String) {
        primitives['$group.$key'] = node['value'] as String;
        if (group == 'core') primitives[key] = node['value'] as String;
      }
    });
  });

  // Flatten alias references: 'primary.default' → '{pink.500}'
  final rawAlias = <String, String>{};
  alias.forEach((group, groupData) {
    if (groupData is! Map<String, dynamic>) return;
    groupData.forEach((key, node) {
      if (node is Map<String, dynamic> && node['value'] is String) {
        rawAlias['$group.$key'] = node['value'] as String;
      }
    });
  });

  // Resolve all alias values through the combined map (handles chain refs)
  final combined = <String, String>{...primitives, ...rawAlias};
  final resolved = {
    ...primitives,
    for (final e in rawAlias.entries) e.key: _resolve(e.value, combined),
  };
  return resolved;
}

String _resolve(String raw, Map<String, String> map) {
  if (!raw.startsWith('{') || !raw.endsWith('}')) return raw;
  final key = raw.substring(1, raw.length - 1);
  final next = map[key];
  if (next == null) return raw;
  return next.startsWith('{') ? _resolve(next, map) : next;
}

/// Recursively flattens a component color group: resolves token refs and
/// renames 'default' → 'base' (Dart reserved word).
Map<String, String> _flatColors(
  Map<String, dynamic> group,
  Map<String, String> colorMap, [
  String prefix = '',
]) {
  const renamed = {'default': 'base'};
  final out = <String, String>{};
  group.forEach((raw, value) {
    if (raw.startsWith(r'$')) return;
    final key = renamed[raw] ?? raw;
    final prop = prefix.isEmpty ? key : '$prefix${_cap(key)}';
    if (value is! Map<String, dynamic>) return;
    if (value.containsKey('value') && value.containsKey('type')) {
      out[prop] = _resolve(value['value'] as String, colorMap);
    } else {
      out.addAll(_flatColors(value, colorMap, prop));
    }
  });
  return out;
}

// ---------------------------------------------------------------------------
// AppColors
// ---------------------------------------------------------------------------

void _generateColors(Map<String, dynamic> data, Map<String, String> colorMap) {
  final light = data['component/light'] as Map<String, dynamic>;
  final dark = data['component/dark'] as Map<String, dynamic>;
  final groups = light.keys.toList();

  final b = StringBuffer();
  b.writeln("import 'package:flutter/material.dart';\n");

  for (final g in groups) {
    final cls = '${_cap(g)}Colors';
    final lf = _flatColors(light[g] as Map<String, dynamic>, colorMap);
    final df = _flatColors(dark[g] as Map<String, dynamic>, colorMap);
    final props = [...lf.keys, ...df.keys.where((k) => !lf.containsKey(k))];
    final nullable = {for (final p in props) p: !lf.containsKey(p) || !df.containsKey(p)};

    b.writeln('class $cls {');
    for (final p in props) {
      b.writeln('  final ${nullable[p]! ? 'Color?' : 'Color'} $p;');
    }
    b.writeln('\n  const $cls({');
    for (final p in props) b.writeln('    required this.$p,');
    b.writeln('  });');

    b.writeln('\n  $cls copyWith({');
    for (final p in props) b.writeln('    Color? $p,');
    b.writeln('  }) {');
    b.writeln('    return $cls(');
    for (final p in props) b.writeln('      $p: $p ?? this.$p,');
    b.writeln('    );');
    b.writeln('  }');

    b.writeln('\n  static $cls lerp($cls? a, $cls? b, double t) {');
    b.writeln("    if (a == null && b == null) throw Exception('lerp called with both null');");
    b.writeln('    if (a == null) return b!;');
    b.writeln('    if (b == null) return a;');
    b.writeln('    return $cls(');
    for (final p in props) {
      if (!nullable[p]!) {
        b.writeln('      $p: Color.lerp(a.$p, b.$p, t) ?? a.$p,');
      } else {
        b.writeln('      $p: Color.lerp(a.$p, b.$p, t),');
      }
    }
    b.writeln('    );');
    b.writeln('  }');
    b.writeln('}\n');
  }

  b.writeln('class AppColors extends ThemeExtension<AppColors> {');
  for (final g in groups) b.writeln('  final ${_cap(g)}Colors $g;');
  b.writeln('\n  const AppColors({');
  for (final g in groups) b.writeln('    required this.$g,');
  b.writeln('  });');

  for (final mode in ['light', 'dark']) {
    final src = mode == 'light' ? light : dark;
    b.writeln('\n  factory AppColors.$mode() {');
    b.writeln('    return const AppColors(');
    for (final g in groups) {
      b.writeln('      $g: ${_cap(g)}Colors(');
      _flatColors(src[g] as Map<String, dynamic>, colorMap)
          .forEach((p, hex) => b.writeln('        $p: ${_hexToColor(hex)},'));
      b.writeln('      ),');
    }
    b.writeln('    );');
    b.writeln('  }');
  }

  b.writeln('\n  @override');
  b.writeln('  AppColors copyWith({');
  for (final g in groups) b.writeln('    ${_cap(g)}Colors? $g,');
  b.writeln('  }) {');
  b.writeln('    return AppColors(');
  for (final g in groups) b.writeln('      $g: $g ?? this.$g,');
  b.writeln('    );');
  b.writeln('  }');

  b.writeln('\n  @override');
  b.writeln('  AppColors lerp(ThemeExtension<AppColors>? other, double t) {');
  b.writeln('    if (other is! AppColors) return this;');
  b.writeln('    return AppColors(');
  for (final g in groups) {
    b.writeln('      $g: ${_cap(g)}Colors.lerp($g, other.$g, t),');
  }
  b.writeln('    );');
  b.writeln('  }');
  b.writeln('}');

  File('lib/theme/app_colors.dart').writeAsStringSync(b.toString());
}

// ---------------------------------------------------------------------------
// AppDimension  — nested: dimension.spacing.s12, dimension.radius.card, etc.
// ---------------------------------------------------------------------------

void _generateDimension(Map<String, dynamic> data) {
  final mobile = data['dimension/mobile'] as Map<String, dynamic>;
  final tablet = data['dimension/tablet'] as Map<String, dynamic>;

  // group name → ordered list of {propName: (mVal, tVal)}
  final groupProps = <String, Map<String, (double, double)>>{};

  // Walk a group recursively, building camelCase prop names WITHOUT group prefix.
  void walkGroup(
    Map<String, dynamic> mG,
    Map<String, dynamic> tG,
    String prefix,
    Map<String, (double, double)> out,
  ) {
    mG.forEach((key, mNode) {
      if (key.startsWith(r'$')) return;
      final safeKey = _safeName(key);
      final propKey = prefix.isEmpty ? safeKey : '$prefix${_cap(safeKey)}';
      final tNode = tG[key];
      if (mNode is Map<String, dynamic> && mNode.containsKey('value')) {
        final mVal = (mNode['value'] as num).toDouble();
        final tVal = tNode is Map<String, dynamic> && tNode.containsKey('value')
            ? (tNode['value'] as num).toDouble()
            : mVal;
        out[propKey] = (mVal, tVal);
      } else if (mNode is Map<String, dynamic>) {
        walkGroup(mNode, tNode is Map<String, dynamic> ? tNode : {}, propKey, out);
      }
    });
  }

  mobile.forEach((group, mGroup) {
    if (group.startsWith(r'$') || mGroup is! Map<String, dynamic>) return;
    final tGroup = tablet[group] is Map<String, dynamic>
        ? tablet[group] as Map<String, dynamic>
        : <String, dynamic>{};
    final props = <String, (double, double)>{};

    if (group == 'spacing') {
      // Numeric keys ('0', '2', '4' …) — prefix with 's'
      mGroup.forEach((key, mNode) {
        if (key.startsWith(r'$') || mNode is! Map<String, dynamic>) return;
        if (!mNode.containsKey('value')) return;
        final tNode = tGroup[key];
        props['s$key'] = (
          (mNode['value'] as num).toDouble(),
          tNode is Map<String, dynamic> && tNode.containsKey('value')
              ? (tNode['value'] as num).toDouble()
              : (mNode['value'] as num).toDouble(),
        );
      });
    } else {
      walkGroup(mGroup, tGroup, '', props);
    }

    groupProps[group] = props;
  });

  // Class name for each group: 'App' + Cap(group) + 'Tokens'
  String cls(String group) => 'App${_cap(group)}Tokens';

  final sb = StringBuffer();
  sb.writeln("import 'package:flutter/material.dart';");
  sb.writeln("import 'dart:ui';\n");

  // Generate a sub-class per dimension group.
  for (final group in groupProps.keys) {
    final props = groupProps[group]!;
    final c = cls(group);
    sb.writeln('class $c {');
    for (final p in props.keys) sb.writeln('  final double $p;');
    sb.writeln('\n  const $c({');
    for (final p in props.keys) sb.writeln('    required this.$p,');
    sb.writeln('  });');
    sb.writeln('\n  static $c lerp($c a, $c b, double t) =>');
    sb.writeln('      $c(');
    for (final p in props.keys) {
      sb.writeln('        $p: lerpDouble(a.$p, b.$p, t) ?? a.$p,');
    }
    sb.writeln('      );');
    sb.writeln('}\n');
  }

  // Generate AppDimension holding all groups.
  final groups = groupProps.keys.toList();
  sb.writeln('class AppDimension extends ThemeExtension<AppDimension> {');
  for (final g in groups) sb.writeln('  final ${cls(g)} $g;');
  sb.writeln('\n  const AppDimension({');
  for (final g in groups) sb.writeln('    required this.$g,');
  sb.writeln('  });');

  for (final factory in ['mobile', 'tablet']) {
    sb.writeln('\n  factory AppDimension.$factory() {');
    sb.writeln('    return const AppDimension(');
    for (final g in groups) {
      final props = groupProps[g]!;
      sb.writeln('      $g: ${cls(g)}(');
      for (final p in props.keys) {
        final v = factory == 'mobile' ? props[p]!.$1 : props[p]!.$2;
        sb.writeln('        $p: $v,');
      }
      sb.writeln('      ),');
    }
    sb.writeln('    );');
    sb.writeln('  }');
  }

  sb.writeln('\n  @override');
  sb.writeln('  AppDimension copyWith({');
  for (final g in groups) sb.writeln('    ${cls(g)}? $g,');
  sb.writeln('  }) {');
  sb.writeln('    return AppDimension(');
  for (final g in groups) sb.writeln('      $g: $g ?? this.$g,');
  sb.writeln('    );');
  sb.writeln('  }');

  sb.writeln('\n  @override');
  sb.writeln(
      '  AppDimension lerp(ThemeExtension<AppDimension>? other, double t) {');
  sb.writeln('    if (other is! AppDimension) return this;');
  sb.writeln('    return AppDimension(');
  for (final g in groups) {
    sb.writeln('      $g: ${cls(g)}.lerp($g, other.$g, t),');
  }
  sb.writeln('    );');
  sb.writeln('  }');
  sb.writeln('}');

  File('lib/theme/app_dimension.dart').writeAsStringSync(sb.toString());
}

// ---------------------------------------------------------------------------
// AppTypography — nested: typography.headline.small, typography.caption, etc.
// ---------------------------------------------------------------------------

// Style name → group it belongs to (null = standalone field on AppTypography).
const _typoGroupOf = <String, String?>{
  'displayHero': 'display',
  'displayLarge': 'display',
  'displayMedium': 'display',
  'displaySmall': 'display',
  'headlineLarge': 'headline',
  'headlineMedium': 'headline',
  'headlineSmall': 'headline',
  'titleLarge': 'title',
  'titleMedium': 'title',
  'titleSmall': 'title',
  'bodyLarge': 'body',
  'bodyMedium': 'body',
  'bodySmall': 'body',
  'labelLarge': 'label',
  'labelMedium': 'label',
  'labelSmall': 'label',
  'caption': null,
  'overline': null,
  'code': null,
};

// Font weights per style (not in the token file — baked from design intent).
const _weights = <String, int>{
  'displayHero': 700,
  'displayLarge': 700,
  'displayMedium': 700,
  'displaySmall': 600,
  'headlineLarge': 600,
  'headlineMedium': 600,
  'headlineSmall': 600,
  'titleLarge': 500,
  'titleMedium': 500,
  'titleSmall': 500,
  'bodyLarge': 400,
  'bodyMedium': 400,
  'bodySmall': 400,
  'labelLarge': 500,
  'labelMedium': 500,
  'labelSmall': 500,
  'caption': 400,
  'overline': 600,
  'code': 400,
};

// Monospace styles use JetBrains Mono; all others use Inter.
const _monoStyles = {'code'};

void _generateTypography(Map<String, dynamic> data) {
  final mobile = data['typography/mobile'] as Map<String, dynamic>;
  final tablet = data['typography/tablet'] as Map<String, dynamic>;

  final styles = mobile.keys.where((k) => !k.startsWith(r'$')).toList();

  double val(Map<String, dynamic> style, String prop) =>
      ((style[prop] as Map<String, dynamic>)['value'] as num).toDouble();

  String buildStyleExpr(String name, Map<String, dynamic> style) {
    final fontSize = val(style, 'fontSize');
    final lineHeight = val(style, 'lineHeight');
    final letterSpacing = val(style, 'letterSpacing');
    final paragraphSpacing = val(style, 'paragraphSpacing');
    final height = lineHeight / fontSize;
    final fw = _weights[name] ?? 400;
    final family = _monoStyles.contains(name) ? 'JetBrains Mono' : 'Inter';
    return "AppTextStyle(\n"
        "          style: TextStyle(\n"
        "            fontFamily: '$family',\n"
        "            fontSize: $fontSize,\n"
        "            height: ${height.toStringAsFixed(4)},\n"
        "            letterSpacing: $letterSpacing,\n"
        "            fontWeight: FontWeight.w$fw,\n"
        "          ),\n"
        "          paragraphSpacing: $paragraphSpacing,\n"
        "        )";
  }

  // Collect groups preserving declaration order.
  final groupNames = <String>[];
  final groupStyles = <String, List<String>>{};
  for (final s in styles) {
    final g = _typoGroupOf[s];
    if (g == null) continue;
    if (!groupStyles.containsKey(g)) {
      groupNames.add(g);
      groupStyles[g] = [];
    }
    groupStyles[g]!.add(s);
  }
  final standalones = styles.where((s) => _typoGroupOf[s] == null).toList();

  // Strip the group prefix from a style name to get the sub-property name.
  // e.g. 'headlineSmall' with group 'headline' → 'small'
  String subProp(String styleName, String group) {
    final rest = styleName.substring(group.length);
    return rest[0].toLowerCase() + rest.substring(1);
  }

  // Class name for a group: 'App' + Cap(group) + 'Styles'
  String groupCls(String group) => 'App${_cap(group)}Styles';

  final sb = StringBuffer();
  sb.writeln("import 'package:flutter/material.dart';");
  sb.writeln("import 'dart:ui';\n");

  // AppTextStyle
  sb.writeln('class AppTextStyle {');
  sb.writeln('  final TextStyle style;');
  sb.writeln(
      '  /// Bottom spacing between paragraph blocks (in logical pixels).');
  sb.writeln(
      '  final double paragraphSpacing;\n');
  sb.writeln(
      '  const AppTextStyle({required this.style, this.paragraphSpacing = 0});\n');
  sb.writeln('  /// Returns the style, optionally overriding its color.');
  sb.writeln('  TextStyle call({Color? color}) =>\n'
      '      color == null ? style : style.copyWith(color: color);\n');
  sb.writeln('  AppTextStyle copyWith({TextStyle? style, double? paragraphSpacing}) =>\n'
      '      AppTextStyle(\n'
      '        style: style ?? this.style,\n'
      '        paragraphSpacing: paragraphSpacing ?? this.paragraphSpacing,\n'
      '      );\n');
  sb.writeln(
      '  static AppTextStyle lerp(AppTextStyle? a, AppTextStyle? b, double t) {');
  sb.writeln(
      "    if (a == null && b == null) throw Exception('lerp called with both null');");
  sb.writeln('    if (a == null) return b!;');
  sb.writeln('    if (b == null) return a;');
  sb.writeln('    return AppTextStyle(');
  sb.writeln('      style: TextStyle.lerp(a.style, b.style, t) ?? a.style,');
  sb.writeln('      paragraphSpacing:');
  sb.writeln(
      '          lerpDouble(a.paragraphSpacing, b.paragraphSpacing, t) ?? a.paragraphSpacing,');
  sb.writeln('    );');
  sb.writeln('  }');
  sb.writeln('}\n');

  // Generate a style group class per group.
  for (final group in groupNames) {
    final members = groupStyles[group]!;
    final c = groupCls(group);
    sb.writeln('class $c {');
    for (final s in members) sb.writeln('  final AppTextStyle ${subProp(s, group)};');
    sb.writeln('\n  const $c({');
    for (final s in members) sb.writeln('    required this.${subProp(s, group)},');
    sb.writeln('  });\n');
    sb.writeln('  static $c lerp($c a, $c b, double t) =>');
    sb.writeln('      $c(');
    for (final s in members) {
      final p = subProp(s, group);
      sb.writeln('        $p: AppTextStyle.lerp(a.$p, b.$p, t),');
    }
    sb.writeln('      );');
    sb.writeln('}\n');
  }

  // AppTypography ThemeExtension.
  sb.writeln('class AppTypography extends ThemeExtension<AppTypography> {');
  for (final g in groupNames) sb.writeln('  final ${groupCls(g)} $g;');
  for (final s in standalones) sb.writeln('  final AppTextStyle $s;');
  sb.writeln('\n  const AppTypography({');
  for (final g in groupNames) sb.writeln('    required this.$g,');
  for (final s in standalones) sb.writeln('    required this.$s,');
  sb.writeln('  });');

  for (final factory in ['mobile', 'tablet']) {
    final src = factory == 'mobile' ? mobile : tablet;
    sb.writeln('\n  factory AppTypography.$factory() {');
    sb.writeln('    return const AppTypography(');
    for (final group in groupNames) {
      final members = groupStyles[group]!;
      sb.writeln('      ${group}: ${groupCls(group)}(');
      for (final s in members) {
        sb.writeln(
            '        ${subProp(s, group)}: ${buildStyleExpr(s, src[s] as Map<String, dynamic>)},');
      }
      sb.writeln('      ),');
    }
    for (final s in standalones) {
      sb.writeln(
          '      $s: ${buildStyleExpr(s, src[s] as Map<String, dynamic>)},');
    }
    sb.writeln('    );');
    sb.writeln('  }');
  }

  sb.writeln('\n  @override');
  sb.writeln('  AppTypography copyWith({');
  for (final g in groupNames) sb.writeln('    ${groupCls(g)}? $g,');
  for (final s in standalones) sb.writeln('    AppTextStyle? $s,');
  sb.writeln('  }) {');
  sb.writeln('    return AppTypography(');
  for (final g in groupNames) sb.writeln('      $g: $g ?? this.$g,');
  for (final s in standalones) sb.writeln('      $s: $s ?? this.$s,');
  sb.writeln('    );');
  sb.writeln('  }');

  sb.writeln('\n  @override');
  sb.writeln(
      '  AppTypography lerp(ThemeExtension<AppTypography>? other, double t) {');
  sb.writeln('    if (other is! AppTypography) return this;');
  sb.writeln('    return AppTypography(');
  for (final g in groupNames) {
    sb.writeln('      $g: ${groupCls(g)}.lerp($g, other.$g, t),');
  }
  for (final s in standalones) {
    sb.writeln('      $s: AppTextStyle.lerp($s, other.$s, t),');
  }
  sb.writeln('    );');
  sb.writeln('  }');
  sb.writeln('}');

  File('lib/theme/app_typography.dart').writeAsStringSync(sb.toString());
}
