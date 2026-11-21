%option noyywrap nodefault
%{
#include <stdio.h>
#include <string.h>

/* Analizador FLEX adaptado al subconjunto Java del traductor académico.
   Formato de salida: TYPE<TAB>LINE<TAB>COLUMN<TAB>JSON_VALUE */
static int current_line = 1;
static int current_column = 1;
static int token_line = 1;
static int token_column = 1;

#define YY_USER_ACTION { \
    token_line = current_line; token_column = current_column; \
    for (int i = 0; i < yyleng; ++i) { \
        if (yytext[i] == '\n') { ++current_line; current_column = 1; } \
        else if (((unsigned char) yytext[i] & 0xc0) != 0x80) { ++current_column; } \
    } \
}

static void print_json_string(const char *value, int len) {
    putchar('"');
    for (int i = 0; i < len; ++i) {
        unsigned char ch = (unsigned char) value[i];
        switch (ch) {
            case '"': fputs("\\\"", stdout); break;
            case '\\': fputs("\\\\", stdout); break;
            case '\n': fputs("\\n", stdout); break;
            case '\r': fputs("\\r", stdout); break;
            case '\t': fputs("\\t", stdout); break;
            default:
                if (ch < 32) printf("\\u%04x", ch);
                else putchar(ch);
        }
    }
    putchar('"');
}

static void emit(const char *type) {
    printf("%s\t%d\t%d\t", type, token_line, token_column);
    print_json_string(yytext, yyleng);
    putchar('\n');
}
%}
%%
"//"[^\n]*          { /* comentario de línea */ }
[ \t\r\n]+         { /* espacios */ }
"int"               { emit("INT"); }
"double"            { emit("DOUBLE"); }
"String"            { emit("STRING_TYPE"); }
"boolean"           { emit("BOOLEAN_TYPE"); }
"true"              { emit("TRUE"); }
"false"             { emit("FALSE"); }
"if"                { emit("IF"); }
"else"              { emit("ELSE"); }
"while"             { emit("WHILE"); }
"System"            { emit("SYSTEM"); }
"out"               { emit("OUT"); }
"println"           { emit("PRINTLN"); }
[0-9]+\.[0-9]+      { emit("NUMBER"); }
[0-9]+              { emit("NUMBER"); }
\"([^\"\\\x00-\x1f]|\\[\"\\nrtbf])*\"  { emit("STRING_LITERAL"); }
[a-zA-Z_][a-zA-Z0-9_]*  { emit("IDENTIFIER"); }
"=="                { emit("EQUAL"); }
"!="                { emit("NOT_EQUAL"); }
">="                { emit("GREATER_EQUAL"); }
"<="                { emit("LESS_EQUAL"); }
"&&"                { emit("AND"); }
"||"                { emit("OR"); }
"+"                 { emit("PLUS"); }
"-"                 { emit("MINUS"); }
"*"                 { emit("MULTIPLY"); }
"/"                 { emit("DIVIDE"); }
"%"                 { emit("MODULO"); }
"="                 { emit("ASSIGN"); }
">"                 { emit("GREATER"); }
"<"                 { emit("LESS"); }
"!"                 { emit("NOT"); }
"("                 { emit("LPAREN"); }
")"                 { emit("RPAREN"); }
"{"                 { emit("LBRACE"); }
"}"                 { emit("RBRACE"); }
";"                 { emit("SEMICOLON"); }
"."                 { emit("DOT"); }
.                   { emit("ERROR"); }
<<EOF>>             { printf("EOF\t%d\t%d\t\"\"\n", current_line, current_column); return 0; }
%%
int main(void) {
    yylex();
    return 0;
}
