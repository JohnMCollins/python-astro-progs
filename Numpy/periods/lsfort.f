	subroutine avevar(data, n, ave, var)
	
	dimension data(n)

	ave = 0.0
	var = 0.0
	do 11 j=1, n
	   ave = ave + data(j)
11	continue
	ave = ave/n

	do 12 j = 1, n
	   s = data(j) - ave
	   var = var + s*s
12	continue
	var = var / (n-1)
	return
	end

	

      SUBROUTINE period(x,y,n,ofac,hifac,px,py,np,nout,jmax,prob)
      INTEGER jmax,n,nout,np,NMAX
      REAL hifac,ofac,prob,px(np),py(np),x(n),y(n)
      PARAMETER (NMAX=2000)
CU    USES avevar
      INTEGER i,j
      REAL ave,c,cc,cwtau,effm,expy,pnow,pymax,s,ss,sumc,sumcy,sums,
     *sumsh,sumsy,swtau,var,wtau,xave,xdif,xmax,xmin,yy
      DOUBLE PRECISION arg,wtemp,wi(NMAX),wpi(NMAX),wpr(NMAX),wr(NMAX),
     *TWOPID
      PARAMETER (TWOPID=6.2831853071795865D0)
      nout=0.5*ofac*hifac*n
      if(nout.gt.np) pause 'output arrays too short in period'
      call avevar(y,n,ave,var)
      xmax=x(1)
      xmin=x(1)
      do 11 j=1,n
        if(x(j).gt.xmax)xmax=x(j)
        if(x(j).lt.xmin)xmin=x(j)
11    continue
      xdif=xmax-xmin
      xave=0.5*(xmax+xmin)
      pymax=0.
      pnow=1./(xdif*ofac)
      do 12 j=1,n
        arg=TWOPID*((x(j)-xave)*pnow)
        wpr(j)=-2.d0*sin(0.5d0*arg)**2
        wpi(j)=sin(arg)
        wr(j)=cos(arg)
        wi(j)=wpi(j)
12    continue
      do 15 i=1,nout
        px(i)=pnow
        sumsh=0.
        sumc=0.
        do 13 j=1,n
          c=wr(j)
          s=wi(j)
          sumsh=sumsh+s*c
          sumc=sumc+(c-s)*(c+s)
13      continue
        wtau=0.5*atan2(2.*sumsh,sumc)
        swtau=sin(wtau)
        cwtau=cos(wtau)
        sums=0.
        sumc=0.
        sumsy=0.
        sumcy=0.
        do 14 j=1,n
          s=wi(j)
          c=wr(j)
          ss=s*cwtau-c*swtau
          cc=c*cwtau+s*swtau
          sums=sums+ss**2
          sumc=sumc+cc**2
          yy=y(j)-ave
          sumsy=sumsy+yy*ss
          sumcy=sumcy+yy*cc
          wtemp=wr(j)
          wr(j)=(wr(j)*wpr(j)-wi(j)*wpi(j))+wr(j)
          wi(j)=(wi(j)*wpr(j)+wtemp*wpi(j))+wi(j)
14      continue
        py(i)=0.5*(sumcy**2/sumc+sumsy**2/sums)/var
        if (py(i).ge.pymax) then
          pymax=py(i)
          jmax=i
        endif
        pnow=pnow+1./(ofac*xdif)
15    continue
      expy=exp(-pymax)
      effm=2.*nout/ofac
      prob=effm*expy
      if(prob.gt.0.01)prob=1.-(1.-expy)**effm
      return
      END
C  (C) Copr. 1986-92 Numerical Recipes Software X!.

C  Main program Fortran L-S, JMC Apr 2015

       integer nmax, rmax, dims, nout, jmax, cnum
       parameter (nmax=1000)
       parameter (rmax=1000000)
       parameter (ndcols=8)
       DOUBLE PRECISION TWOPID
       PARAMETER (TWOPID=6.2831853071795865D0)

       real x(nmax), y(nmax), tn(ndcols), ofac, hifac
       real resx(rmax), resy(rmax), prob, scale, nyfreq
       character*64 infile, outfile, cofac, chifac, cscl, ctyp

       dims = iargc()
       if (dims .ne. 6) then
            write(*,*) 'Usage: lombs infile outfile ofac hifac sc ty'
            call exit(10)
       end if

       call getarg(1, infile)
       call getarg(2, outfile)
       call getarg(3, cofac)
       call getarg(4, chifac)
       call getarg(5, cscl)
       call getarg(6, ctyp)
       read (cofac, *) ofac
       read (chifac, *) hifac
       read (cscl, *) scale

       if (ctyp .eq. 'ew') then
            cnum = 3
       else
        if (ctyp .eq. 'ps') then
            cnum = 5
        else
            if (ctyp .eq. 'pr') then
                cnum = 7
            else
                write(*,*) 'Unknown type expecting ew,ps,pr'
                call exit(11)
            end if
        end if
       end if

       open(17, file=infile)
       open(18, file=outfile)
       dims = 0
       do 10 i=1, nmax
          read(17, *, end=30) tn
          x(i) = tn(1)
          y(i) = tn(cnum)
          dims = dims + 1
10        continue
30     continue

       nyfreq = dims / (2.0 * (x(dims) - x(1)))
       write (*,*) 'Nyfreq=', nyfreq

       if (scale .ne. 1.0) then
       do 40 i = 1, nmax
40     x(i) = x(i) * scale
       end if

       call period(x, y, dims, ofac, hifac, resx, resy, rmax, nout,
     *             jmax, prob)

       do 50 i = 1, nout
50     write(18, 51) scale * nyfreq * TWOPID / resx(i), resy(i)
51     format(2E25.16)
       write(*,*) 'nout = ', nout,'  jmax = ', jmax, '  prob = ', prob
       stop
       end
