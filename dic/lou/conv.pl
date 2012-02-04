#!/usr/bin/perl -w

# Usage: cat mecab-ipadic-2.7.0-20060707/*.csv | ./conv.pl > dic.csv

# http://e8y.net/repos/Lingua-JA-Japaninglish/trunk/bep/bep-eng.dic
open(F, "nkf -e bep-eng.dic|") || die;
while(<F>) {
    next if (/shift_jis/);
    chomp;
    my ($from, $to) = split;
    $from = lc($from);
    $j2j{$from} = $to;
}
close(F);

open(F, "nkf -e edict|") || die;
while (<F>) {
    chomp;
    $_ = lc($_);
    s/\([^\)]+\)//g;
    s/\[[^\]]+\]//g;
    s#\s+/#/#g;
    s#/\s+#/#g;
    my $line = $_;
    my @list = split "/", $_;
    my $w = shift @list;
    next if ($w eq "¤¤¤¯");
    for (@list) {
        next if ($_ eq "");
        s/^to //;
        s/^be //;
        my @words = split / /, $_;
        my @towords;
        for my $t (@words) {
            if (defined $j2j{$t}) {
                push @towords, $j2j{$t}; 
            }
        }
        if (scalar(@words) == scalar(@towords)) {
            my $p = join "", @towords;
            $dic{$w} = $p;
            last;
        }
        if (defined $j2j{$_}) {
            $dic{$w} = $j2j{$_};
            last;
        }

    }
}
close(F);

open(F, "cform") || die;
while (<F>) {
    chomp;
    s/\s+$//g;
    my ($w, $f) = split /\s+/, $_;
    $cform{$w} = $f;
}

while (<>) {
    chomp;
    my @c = split /,/, $_;
    my $to = $dic{$c[10]};
    if (length($c[10]) >= 3 &&
        $c[4] =~ /^(Ì¾»ì|Æ°»ì|·ÁÍÆ»ì|Ï¢ÂÎ»ì)/ && defined $to) {
        my $cf = $cform{"$c[4]-$c[9]"};
#        print "$c[4]-$c[9]\n";
        $to .= $cf if (defined $cf);
        print "$c[0],$c[1],$c[2],$c[3],$to\n";
    } else {
        print "$c[0],$c[1],$c[2],$c[3],$c[0]\n";
    }
}
