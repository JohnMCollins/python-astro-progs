#! /usr/bin/perl

use dbops;
use remdefaults;
use Getopt::Long;
use Pod::Usage;

my $year;
my $month;
my $filter;
my $type;
my $outfile;
my $help;
my $forward = 0;
my $backward = 0;
my $dbname = remdefaults::default_database;

GetOptions("database=s" => \$dbname, 
           "year=i" => \$year,
           "month=i" => \$month,
           "filter=s", \$filter,
           "type=s" => \$type,
           "outfile=s" => \$outfile,
           "forward=i" => \$forward,
           "backward=i" => \$backward,
           'help' => \$help) or pod2usage(2);

pod2usage(-exitval => 0, -verbose => 2) if $help;

unless ($year)  {
    print STDERR "No year given\n";
    exit 10;
}

unless ($month)  {
    print STDERR "No month given\n";
    exit 11;
}

unless ($filter)  {
    print STDERR "No filter given\n";
    exit 12;
}

unless ($type)  {
    print STDERR "No type given\n";
    exit 13;
}

unless ($filter =~ /^[griz]$/)  {
    print STDERR "Unknown filter type $filter\n";
    exit 14;
}

unless ($type =~ /^([fb])/)  {
    print STDERR "Unknown file type $type\n";
    exit 15;
}

unless ($outfile) {
    print STDERR "No output file given\n";
    exit 16;
}

$type = lc $1;
if ($type eq 'f') {
    $type = 'flat';
}
else {
    $type = 'bias';
}

my $dbase = dbops::opendb($dbname) or die "Cannot open DB $dbname";

my $sfh = $dbase->prepare("SELECT fitsind FROM forbinf WHERE year=$year AND month=$month AND typ='$type' AND filter='$filter'");
$sfh->execute;
my $row = $sfh->fetchrow_arrayref;

unless ($row)  {
    my $fstep = 0;
    my $bstep = 0;
    my $combdate = $year * 12 + $month - 1;
    
    while  ($fstep < $forward || $bstep < $backward)  {
        
        if ($fstep < $forward)  {
            $fstrep++;
            my $rd = $combdate + $fstep;
            my $y = int($rd / 12);
            my $m = $rd % 12 + 1;
            $sfh = $dbase->prepare("SELECT fitsind FROM forbinf WHERE year=$y AND month=$m AND typ='$type' AND filter='$filter'");
            $sfh->execute;
            $row = $sfh->fetchrow_arrayref;
            if ($row)  {
                print "Actually selected $m/$y\n";
                last;
            }
        }
        
        if ($bstep < $backward)  {
            $bstep++;
            my $rd = $combdate - $bstep;
            my $y = int($rd / 12);
            my $m = $rd % 12 + 1;
            $sfh = $dbase->prepare("SELECT fitsind FROM forbinf WHERE year=$y AND month=$m AND typ='$type' AND filter='$filter'");
            $sfh->execute;
            $row = $sfh->fetchrow_arrayref;
            if ($row)  {
                print "Actually selected $m/$y\n";
                last;
            }
        }
    }
    
    unless ($row)  {
       print STDERR "Cannot find specified $type file\n";
        exit 20;
    }
}

my $fitsind = $row->[0];
unless ($fitsind != 0) {
	print STDERR "No FITS file held for specified $type filen";
	exit 23;
}
$sfh = $dbase->prepare("SELECT fitsgz FROM fitsfile WHERE ind=$fitsind");
$sfh->execute;
$row = $sfh->fetchrow_arrayref;
my $fits = $row->[0];

open(OUTF, ">$outfile") or die "Cannot create output file $outfile";
my $offs = 0;
my $nbytes = length $fits;
while ($nbytes > 0)  {
    my $nout = 4096;
    $nout = $nbytes if $nout > $nbytes;
    my $nput = syswrite OUTF, $fits, $nout, $offs;
    $offs += $nput;
    $nbytes -= $nput;
}
close OUTF;
exit 0;


__END__

=head1 NAME

fetrchforb - - Get monthly flat or bias file from database

=head1 SYNOPSIS

fetchfits options

  
=head1 OPTIONS

Nearly all the options are actually required.
 
=over 8
 
=item B<-help>
 
 Print a brief help message and exit.
 
=item B<-year> integer
 
 Specify the required year.
 
=item B<-month> integer
 
 Specify the required month.

=item B<-type> f/b

 Specify the required type, flat or bias
 
=item B<-filter> g/r/i/z

 Specify the required filter type

=item B<-outfile> filename

 Specify the required output file name (probably should end in .gz)
 
=item B<-forward> n

 If the file cannot be found try successive months forward up to n.

=item B<-backward> n

 If the file cannot be found try successive months backward up to n.
 
=back

If both -forward and -backward ptions are given, the forward and backward steps are tried alternately until a file is found.

=head1 DESCRIPTION

This program copies the required flat or bias file to the specified output file


