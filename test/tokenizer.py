import sys
import pysynphot.spparser as p

def print_token_list(l) :
    for x in l : 
        print "%-20s "% x.type, x.attr
    print ""


# Test of a single instance of each token.  does not test them in
# context, but at least it tests that each one is recognized.

tokens = [
    # bug: the original pysynphot could not recognize integer
    # ('INTEGER', '1'),

    # basic float
    ('FLOAT',   '.1'),
    ('FLOAT',   '1.1'),
    ('FLOAT',   '1.'),
    ('FLOAT',   '1'),

    # basic float with e+
    ('FLOAT',   '.1e+1'),
    ('FLOAT',   '1.1e+1'),
    ('FLOAT',   '1.e+1'),
    ('FLOAT',   '1e+1'),

    # basic float with e-
    ('FLOAT',   '.1e-1'),
    ('FLOAT',   '1.1e-1'),
    ('FLOAT',   '1.e-1'),
    ('FLOAT',   '1e-1'),

    # basic float with e
    ('FLOAT',   '.1e1'),
    ('FLOAT',   '1.1e1'),
    ('FLOAT',   '1.e1'),
    ('FLOAT',   '1e1'),

    # identifier
    ('IDENTIFIER',  'xyzzy'),
    ('IDENTIFIER',  'xyzzy20'),
    ('IDENTIFIER',  '20xyzzy'),
    ('IDENTIFIER',  '20xyzzy20'),

    # special characters
    ('LPAREN',  '('),
    ('RPAREN',  ')'),
    (',',       ','),
    ('/',       ' / '),

    # filename
    ('IDENTIFIER',  '/a/b/c'),
    ('IDENTIFIER',  'foo$bar'),
    ('IDENTIFIER',  'a/b'),

    # file list
    ('FILELIST',    '@arf'),
    ('FILELIST',    '@narf'),

]



scanner = p.Scanner()

def test_tokens() :
    fail = 0

    for x in tokens :
        print "XXXX",x
        typ, val = x
        l = scanner.tokenize(val)
        print "tokens:",len(l)
        print_token_list(l)

        if not len(l) == 1 :
            print "too many tokens"
            fail = 1

        if not l[0].type == typ :
            print "wrong type"
            fail = 1

        if not (
                ( l[0].attr == val ) 
            or  ( l[0].attr is None ) 
            or  ( val.startswith('@') and ( l[0].attr == val[1:] ) )
            ) :
            print "token value incorrect"
            fail = 1
        
    assert not fail


# use this to generate the list of tokens in a form easy to copy/paste
# into a test
def ptl2(l) :
    for x in l : 
        print " ( '%s', %s ),  "% ( x.type, repr(x.attr ) )
    print ""

def stream_t( text, result ) :
    l = scanner.tokenize( text )
    print_token_list(l)
    for x,y in zip(result,l) :
        print "x=",x
        print "y=",y
        assert x[0] == y.type
        assert x[1] == y.attr


def test_stream_a() :
    stream_t('spec($PYSYN_CDBS//calspec/gd71_mod_005.fits)',
        [
        ( 'IDENTIFIER', 'spec' ),  
        ( 'LPAREN', None ),  
        ( 'IDENTIFIER', '$PYSYN_CDBS//calspec/gd71_mod_005.fits' ),  
        ( 'RPAREN', None ),  
        ] )

def test_stream_b() :
    stream_t('rn(unit(1.,flam),band(stis,ccd,g430m,c4451,52X0.2),10.000000,abmag)',
        [
        ( 'IDENTIFIER', 'rn' ),  
        ( 'LPAREN', None ),  
        ( 'IDENTIFIER', 'unit' ),  
        ( 'LPAREN', None ),  
        ( 'FLOAT', '1.' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'flam' ),  
        ( 'RPAREN', None ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'band' ),  
        ( 'LPAREN', None ),  
        ( 'IDENTIFIER', 'stis' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'ccd' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'g430m' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'c4451' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', '52X0.2' ),  
        ( 'RPAREN', None ),  
        ( ',', None ),  
        ( 'FLOAT', '10.000000' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'abmag' ),  
        ( 'RPAREN', None ),  
        ] )

def test_stream_c() :
    stream_t( 'rn(unit(1.,flam),band(stis,ccd,mirror,50CCD),10.000000,abmag)',
        [
        ( 'IDENTIFIER', 'rn' ),  
        ( 'LPAREN', None ),  
        ( 'IDENTIFIER', 'unit' ),  
        ( 'LPAREN', None ),  
        ( 'FLOAT', '1.' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'flam' ),  
        ( 'RPAREN', None ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'band' ),  
        ( 'LPAREN', None ),  
        ( 'IDENTIFIER', 'stis' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'ccd' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'mirror' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', '50CCD' ),  
        ( 'RPAREN', None ),  
        ( ',', None ),  
        ( 'FLOAT', '10.000000' ),  
        ( ',', None ),  
        ( 'IDENTIFIER', 'abmag' ),  
        ( 'RPAREN', None ),  
        ]) 

