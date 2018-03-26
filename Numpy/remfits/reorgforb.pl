#! /usr/bin/perl

use dbops;
use strict;

my $dbase = dbops::opendb('remfits') or die "Cannot open DB";

my $sfh = $dbase->prepare("SELECT year,month,filter,typ,fitsgz FROM forb");
$sfh->execute;

while (my $row = $sfh->fetchrow_arrayref())  {
    
    my ($year, $month, $filter, $typ, $fitsgz) = @$row;
    
    my $ind = 0;
    if (length($fitsgz) != 0)  {
        my $ifh = $dbase->prepare("INSERT INTO fitsfile (fitsgz) VALUES (?)");
        $ifh->execute($fitsgz);
        $ifh = $dbase->prepare("SELECT LAST_INSERT_ID()");
        $ifh->execute;
        my $rr = $ifh->fetchrow_arrayref();
        $ind = $rr->[0];
    }
    
    my $qfilt = $dbase->quote($filter);
    my $qtyp = $dbase->quote($typ);
    my $iofb = $dbase->prepare("INSERT INTO forbinf (year,month,filter,typ,fitsind) VALUES ($year,$month,$qfilt,$qtyp,$ind)");
    $iofb->execute;
}
